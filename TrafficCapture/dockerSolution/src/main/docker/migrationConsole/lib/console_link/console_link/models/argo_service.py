import time
import json
import logging
import tempfile
import os
import uuid
import yaml
from typing import Optional, Dict, Any

from console_link.models.cluster import Cluster
from console_link.models.command_runner import CommandRunner, CommandRunnerError, FlagOnlyArgument

logger = logging.getLogger(__name__)

ENDING_ARGO_PHASES = ["Succeeded", "Failed", "Error", "Stopped", "Terminated"]


class WorkflowEndedBeforeSuspend(Exception):
    def __init__(self, workflow_name: str, phase: str):
        super().__init__(f"The workflow '{workflow_name}' reached ending phase of {phase} before reaching "
                         f"suspend state")


class ArgoServiceError(Exception):
    """Base exception for ArgoService errors"""
    pass


class WorkflowStartError(ArgoServiceError):
    """Error when starting a workflow"""
    pass


class WorkflowOperationError(ArgoServiceError):
    """Error when performing workflow operations"""
    pass


class WorkflowStatusError(ArgoServiceError):
    """Error when getting workflow status"""
    pass


class ArgoService:
    def __init__(self, namespace: str = "ma", argo_image: str = "quay.io/argoproj/argocli:v3.6.5",
                 service_account: str = "argo-workflow-executor"):
        self.namespace = namespace
        self.argo_image = argo_image
        self.service_account = service_account

    def start_workflow(self, workflow_template_name: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        try:
            # Create temporary workflow file
            temp_file = self._create_workflow_yaml(workflow_template_name, parameters)

            # Use kubectl create to start the workflow
            kubectl_args = {
                "create": FlagOnlyArgument,
                "-f": temp_file,
                "--namespace": self.namespace,
                "-o": "jsonpath={.metadata.name}"
            }
            
            result = self._run_kubectl_command(kubectl_args)
            
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except OSError:
                logger.warning(f"Failed to delete temporary file: {temp_file}")

            name = result.stdout.strip()
            logger.info(f"Started workflow: {name}")
            self._wait_for_workflow_exists(workflow_name=name)
            return name
            
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            raise WorkflowStartError(f"Failed to start workflow: {e}") from e

    def resume_workflow(self, workflow_name: str) -> None:
        args = {
            "resume": workflow_name
        }
        self._run_argo_command(pod_action="resume-workflow", argo_args=args)
        logger.info(f"Argo workflow '{workflow_name}' has been resumed")

    def stop_workflow(self, workflow_name: str) -> None:
        args = {
            "stop": workflow_name
        }
        self._run_argo_command(pod_action="stop-workflow", argo_args=args)
        logger.info(f"Argo workflow '{workflow_name}' has been stopped")

    def delete_workflow(self, workflow_name: str) -> None:
        kubectl_args = {
            "delete": FlagOnlyArgument,
            "workflow": workflow_name,
            "--namespace": self.namespace
        }
        self._run_kubectl_command(kubectl_args)
        logger.info(f"Argo workflow '{workflow_name}' has been deleted")

    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        workflow_data = self._get_workflow_status_json(workflow_name)
        phase = workflow_data.get("status", {}).get("phase", "")

        # Check for suspended nodes
        nodes = workflow_data.get("status", {}).get("nodes", {})
        has_suspended_nodes = False
        for node_id, node in nodes.items():
            if node.get("phase") == "Running":
                if node.get("type", "") == "Suspend":
                    has_suspended_nodes = True

        status_info = {
            "phase": phase,
            "has_suspended_nodes": has_suspended_nodes
        }

        logger.info(f"Workflow {workflow_name} status: {status_info}")

        return status_info

    def wait_for_suspend(self, workflow_name: str, timeout_seconds: int = 120, interval: int = 5) -> None:
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                status_info = self.get_workflow_status(workflow_name)
            except Exception as e:
                raise WorkflowStatusError(f"Failed to get workflow status: {e}") from e
                
            phase = status_info.get("phase", "")
            has_suspended_nodes = status_info.get("has_suspended_nodes", False)

            if phase == "Running" and has_suspended_nodes:
                logger.info(f"Workflow {workflow_name} is in a suspended state")
                return
            elif phase in ENDING_ARGO_PHASES:
                raise WorkflowEndedBeforeSuspend(workflow_name=workflow_name, phase=phase)

            time.sleep(interval)

        raise TimeoutError(f"Workflow did not reach suspended state in timeout of {timeout_seconds} seconds")

    def is_workflow_completed(self, workflow_name: str) -> bool:
        try:
            status_info = self.get_workflow_status(workflow_name)
        except Exception as e:
            raise WorkflowStatusError(f"Failed to get workflow status: {e}") from e

        phase = status_info.get("phase", "")

        if phase in ENDING_ARGO_PHASES:
            logger.info(f"Workflow {workflow_name} has reached an ending phase of {phase}")
            return True
        logger.info(f"Workflow {workflow_name} has not completed and is in {phase} phase")
        return False

    def wait_for_ending_phase(self, workflow_name: str, timeout_seconds: int = 120, interval: int = 5) -> str:
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if self.is_workflow_completed(workflow_name):
                status_info = self.get_workflow_status(workflow_name)
                return status_info.get("phase", "")
            time.sleep(interval)

        raise TimeoutError(f"Workflow did not reach ending state in timeout of {timeout_seconds} seconds")

    def watch_workflow(self, workflow_name: str, stream_output: bool = True) -> None:
        argo_args = {
            "logs": workflow_name,
            "--follow": FlagOnlyArgument
        }
        self._run_argo_command(pod_action="watch-workflow", argo_args=argo_args, print_output=stream_output,
                              stream_output=stream_output)

    def get_source_cluster_from_workflow(self, workflow_name: str) -> Cluster:
        return self._get_cluster_config_from_workflow(workflow_name, "source")

    def get_target_cluster_from_workflow(self, workflow_name: str) -> Cluster:
        return self._get_cluster_config_from_workflow(workflow_name, "target")

    def _run_argo_command(self, pod_action: str, argo_args: Dict, print_output: bool = False,
                          stream_output: bool = False):
        pod_name = f"argo-{pod_action}-{uuid.uuid4().hex[:6]}"
        command_args = {
            "run": pod_name,
            "--namespace": self.namespace,
            "--image": self.argo_image,
            "--rm": FlagOnlyArgument,
            "-i": FlagOnlyArgument,
            "--overrides": '{"spec":{"serviceAccountName":"argo-workflow-executor"}}',
            "--restart": "Never",
            "--": FlagOnlyArgument,
        }
        command_args.update(argo_args)
        
        runner = CommandRunner("kubectl", command_args)
        try:
            return runner.run(print_to_console=print_output, stream_output=stream_output)
        except CommandRunnerError as e:
            logger.error(f"Argo command failed: {e}")
            raise WorkflowOperationError(f"Argo command failed: {e}") from e

    def _run_kubectl_command(self, kubectl_args: Dict[str, Any], print_output: bool = False):
        runner = CommandRunner("kubectl", kubectl_args)
        try:
            return runner.run(print_to_console=print_output)
        except CommandRunnerError as e:
            logger.error(f"Kubectl command failed: {e}")
            raise WorkflowOperationError(f"Kubectl command failed: {e}") from e

    def _create_workflow_yaml(self, workflow_template_name: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Create a temporary workflow YAML file based on the template structure."""
        workflow_data = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": f"{workflow_template_name}-"
            },
            "spec": {
                "workflowTemplateRef": {
                    "name": workflow_template_name
                },
                "entrypoint": "main"
            }
        }
        
        # Add parameters if provided
        if parameters:
            workflow_data["spec"]["arguments"] = {
                "parameters": [
                    {
                        "name": key,
                        "value": (
                            json.dumps(value, indent=2)
                            if isinstance(value, (dict, list)) else value
                        )
                    }
                    for key, value in parameters.items()
                ]
            }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(workflow_data, f, default_flow_style=False, sort_keys=False)
            temp_file_path = f.name
        
        # Log created file contents
        try:
            with open(temp_file_path, 'r') as f:
                file_contents = f.read()
                logger.info(f"Created workflow YAML file at {temp_file_path}:\n{file_contents}")
        except Exception as e:
            logger.warning(f"Failed to read temporary file for debugging: {e}")
        
        return temp_file_path

    def _wait_for_workflow_exists(self, workflow_name: str, timeout_seconds: int = 15,
                                  interval: int = 1) -> None:
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            kubectl_args = {
                "get": FlagOnlyArgument,
                "workflow": workflow_name,
                "--namespace": self.namespace,
                "--ignore-not-found": FlagOnlyArgument
            }

            try:
                result = self._run_kubectl_command(kubectl_args)
                if result.stdout.strip():
                    logger.info(f"Workflow {workflow_name} exists")
                    return
            except Exception:
                pass

            time.sleep(interval)

        raise TimeoutError(f"Timeout waiting for workflow {workflow_name} to exist")

    def _get_workflow_status_json(self, workflow_name: str) -> Dict[str, Any]:
        kubectl_args = {
            "get": FlagOnlyArgument,
            "workflow": workflow_name,
            "-o": "json",
            "--namespace": self.namespace
        }
        result = self._run_kubectl_command(kubectl_args)
        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse 'kubectl get workflow <name> -o json' output: {e}")
            raise
        return data

    def _get_cluster_config_from_workflow(self, workflow_name: str, cluster_type: str) -> Cluster:
        workflow_data = self._get_workflow_status_json(workflow_name)
        nodes = workflow_data.get("status", {}).get("nodes", {})
        search = f"create-{cluster_type}-cluster"

        # find the succeeded node that created this cluster
        node = next(
            (
                n for n in nodes.values()
                if search in n.get("displayName", n.get("name", "")) and n.get("phase") == "Succeeded"
            ),
            None,
        )
        if not node:
            raise ValueError(f"Did not find {cluster_type} cluster config")

        params = node.get("outputs", {}).get("parameters", []) or []
        cfg_str = next((p.get("value") for p in params if p.get("name") == "cluster-config"), None)
        if not cfg_str:
            raise ValueError(f"Did not find {cluster_type} cluster config")

        try:
            cfg = json.loads(cfg_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {cluster_type} cluster config JSON: {e}")
            raise

        logger.info(f"Found {cluster_type} cluster config: {cfg}")
        return Cluster(config=cfg)
