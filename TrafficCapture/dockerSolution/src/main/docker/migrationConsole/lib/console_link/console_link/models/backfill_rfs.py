from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from typing import Dict, Optional


import requests

from console_link.models.snapshot import Snapshot, S3Snapshot
from console_link.models.step_state import StepStateWithPause
from console_link.models.backfill_base import Backfill, BackfillOverallStatus, BackfillStatus, DeepStatusNotYetAvailable
from console_link.models.client_options import ClientOptions
from console_link.models.cluster import Cluster, HttpMethod
from console_link.models.schema_tools import contains_one_of
from console_link.models.command_result import CommandResult
from console_link.models.kubectl_runner import DeploymentStatus, KubectlRunner
from console_link.models.ecs_service import ECSService
from console_link.models.argo_service import ArgoService, ENDING_ARGO_PHASES

from cerberus import Validator

import logging

logger = logging.getLogger(__name__)

WORKING_STATE_INDEX = ".migrations_working_state"

DOCKER_RFS_SCHEMA = {
    "type": "dict",
    "nullable": True,
    "schema": {
        "socket": {"type": "string", "required": False}
    }
}


ECS_RFS_SCHEMA = {
    "type": "dict",
    "schema": {
        "cluster_name": {"type": "string", "required": True},
        "service_name": {"type": "string", "required": True},
        "aws_region": {"type": "string", "required": False}
    }
}

K8S_RFS_SCHEMA = {
    "type": "dict",
    "schema": {
        "namespace": {"type": "string", "required": True},
        "deployment_name": {"type": "string", "required": True}
    }
}

ARGO_RFS_SCHEMA = {
    "type": "dict",
    "schema": {
        "namespace": {"type": "string", "required": False, "default": "ma"},
        "workflow_template_name": {"type": "string", "required": True},
        "parameters": {"type": "dict", "required": False}
    }
}

RFS_BACKFILL_SCHEMA = {
    "reindex_from_snapshot": {
        "type": "dict",
        "schema": {
            "docker": DOCKER_RFS_SCHEMA,
            "ecs": ECS_RFS_SCHEMA,
            "k8s": K8S_RFS_SCHEMA,
            "argo": ARGO_RFS_SCHEMA,
            "snapshot_name": {"type": "string", "required": False},
            "snapshot_repo": {"type": "string", "required": False},
            "session_name": {"type": "string", "required": False},
            "scale": {"type": "integer", "required": False, "min": 1}
        },
        "check_with": contains_one_of({'docker', 'ecs', 'k8s', 'argo'}),
    }
}


class RFSBackfill(Backfill):
    def __init__(self, config: Dict) -> None:
        super().__init__(config)

        v = Validator(RFS_BACKFILL_SCHEMA)
        if not v.validate(self.config):
            raise ValueError("Invalid config file for RFS backfill", v.errors)

    def create(self, *args, **kwargs) -> CommandResult:
        return CommandResult(True, "no-op")

    def start(self, *args, **kwargs) -> CommandResult:
        raise NotImplementedError()

    def stop(self, *args, **kwargs) -> CommandResult:
        raise NotImplementedError()

    def get_status(self, *args, **kwargs) -> CommandResult:
        raise NotImplementedError()

    def scale(self, units: int, *args, **kwargs) -> CommandResult:
        raise NotImplementedError()


class DockerRFSBackfill(RFSBackfill):
    def __init__(self, config: Dict, target_cluster: Cluster) -> None:
        super().__init__(config)
        self.target_cluster = target_cluster
        self.docker_config = self.config["reindex_from_snapshot"]["docker"]

    def pause(self, pipeline_name=None) -> CommandResult:
        raise NotImplementedError()

    def get_status(self, *args, **kwargs) -> CommandResult:
        return CommandResult(True, (BackfillStatus.RUNNING, "This is my running state message"))

    def scale(self, units: int, *args, **kwargs) -> CommandResult:
        raise NotImplementedError()
    
    def archive(self, *args, **kwargs) -> CommandResult:
        raise NotImplementedError()

    def build_backfill_status(self, *args) -> BackfillStatus:
        raise NotImplementedError()
    

class RfsWorkersInProgress(Exception):
    def __init__(self):
        super().__init__("RFS Workers are still in progress")


class WorkingIndexDoesntExist(Exception):
    def __init__(self, index_name: str):
        super().__init__(f"The working state index '{index_name}' does not exist")


class K8sRFSBackfill(RFSBackfill):
    def __init__(self, config: Dict, target_cluster: Cluster, client_options: Optional[ClientOptions] = None) -> None:
        super().__init__(config)
        self.client_options = client_options
        self.target_cluster = target_cluster
        self.default_scale = self.config["reindex_from_snapshot"].get("scale", 5)

        self.k8s_config = self.config["reindex_from_snapshot"]["k8s"]
        self.namespace = self.k8s_config["namespace"]
        self.deployment_name = self.k8s_config["deployment_name"]
        self.kubectl_runner = KubectlRunner(namespace=self.namespace, deployment_name=self.deployment_name)

    def start(self, *args, **kwargs) -> CommandResult:
        logger.info(f"Starting RFS backfill by setting desired count to {self.default_scale} instances")
        return self.kubectl_runner.perform_scale_command(replicas=self.default_scale)

    def pause(self, *args, **kwargs) -> CommandResult:
        logger.info("Pausing RFS backfill by setting desired count to 0 instances")
        return self.kubectl_runner.perform_scale_command(replicas=0)

    def stop(self, *args, **kwargs) -> CommandResult:
        logger.info("Stopping RFS backfill by setting desired count to 0 instances")
        return self.kubectl_runner.perform_scale_command(replicas=0)

    def scale(self, units: int, *args, **kwargs) -> CommandResult:
        logger.info(f"Scaling RFS backfill by setting desired count to {units} instances")
        return self.kubectl_runner.perform_scale_command(replicas=units)

    def archive(self, *args, archive_dir_path: str = None, archive_file_name: str = None, **kwargs) -> CommandResult:
        deployment_status = self.kubectl_runner.retrieve_deployment_status()
        return perform_archive(target_cluster=self.target_cluster,
                               deployment_status=deployment_status,
                               archive_dir_path=archive_dir_path,
                               archive_file_name=archive_file_name)

    def get_status(self, deep_check=False, *args, **kwargs) -> CommandResult:
        logger.info("Getting status of RFS backfill")
        deployment_status = self.kubectl_runner.retrieve_deployment_status()
        if not deployment_status:
            return CommandResult(False, "Failed to get deployment status for RFS backfill")
        status_str = str(deployment_status)
        if deep_check:
            try:
                shard_status = get_detailed_status(target_cluster=self.target_cluster)
            except Exception as e:
                logger.error(f"Failed to get detailed status: {e}")
                shard_status = None
            if shard_status:
                status_str += f"\n{shard_status}"
        if deployment_status.terminating > 0 and deployment_status.desired == 0:
            return CommandResult(True, (BackfillStatus.TERMINATING, status_str))
        if deployment_status.running > 0:
            return CommandResult(True, (BackfillStatus.RUNNING, status_str))
        if deployment_status.pending > 0:
            return CommandResult(True, (BackfillStatus.STARTING, status_str))
        return CommandResult(True, (BackfillStatus.STOPPED, status_str))
    
    def build_backfill_status(self) -> BackfillOverallStatus:
        deployment_status = self.kubectl_runner.retrieve_deployment_status()
        active_workers = True  # Assume there are active workers if we cannot lookup the deployment status
        if deployment_status is not None:
            active_workers = deployment_status.desired != 0
        return get_detailed_status_obj(self.target_cluster, active_workers)


class ArgoRFSBackfill(RFSBackfill):
    """
    Implementation of RFS backfill using Argo Workflows to control the document bulk load process.
    This class leverages Argo Workflows to manage the reindex-from-snapshot workflow template.
    
    The workflow template should have an entrypoint template named 'run-bulk-load' or 'run-bulk-load-from-config'
    and should accept the parameters as specified in documentBulkLoad.yaml.
    """
    def __init__(self, config: Dict, snapshot: Optional[Snapshot], target_cluster: Cluster,
                 client_options: Optional[ClientOptions] = None) -> None:
        super().__init__(config)
        self.client_options = client_options
        self.target_cluster = target_cluster
        
        if snapshot is None:
            raise ValueError("A snapshot object is required for ArgoRFSBackfill")
        self.snapshot = snapshot
        
        # Extract Argo configuration
        self.argo_config = self.config["reindex_from_snapshot"]["argo"]
        self.namespace = self.argo_config.get("namespace", "ma")
        self.workflow_template_name = self.argo_config["workflow_template_name"]
        
        # Initialize parameters dictionary
        self.parameters = self._initialize_parameters()
        
        # Initialize the ArgoService
        self.argo_service = ArgoService(namespace=self.namespace)
        
        # Track the workflow name once started
        # TODO: This does not work at all, need to use the new workflow DB
        self.workflow_name = None

    def _initialize_parameters(self) -> Dict:
        """
        Initialize and prepare all parameters needed for the workflow.
        
        Returns:
            Dictionary of parameters to pass to the workflow
        """
        # Start with any existing parameters from config
        parameters = self.argo_config.get("parameters", {}).copy()
        
        # Set session name if not provided
        if "session-name" not in parameters:
            session_name = self.config["reindex_from_snapshot"].get(
                "session_name", 
                f"rfs-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            parameters["session-name"] = session_name
            
        # Add snapshot configuration - we've validated snapshot is not None in __init__
        parameters["snapshot-name"] = self.snapshot.snapshot_name
        logger.debug(f"Using snapshot: {self.snapshot.snapshot_name}")
        
        # Add S3 specific parameters if needed
        if isinstance(self.snapshot, S3Snapshot):
            parameters["s3-repo-uri"] = self.snapshot.s3_repo_uri
            parameters["s3-region"] = self.snapshot.s3_region
            parameters["s3-endpoint"] = self.snapshot.s3_endpoint
            
        # Add target cluster parameters
        parameters["target-host"] = self.target_cluster.endpoint
        parameters["target-insecure"] = self.target_cluster.allow_insecure
        parameters["target-username"] = self.target_cluster.auth_details["username"]
        parameters["target-password"] = self.target_cluster.auth_details["password"]
        
        # Add additional configuration parameters
        if "target-config" not in parameters:
            parameters["target-config"] = json.dumps(self.target_cluster.config)
            
        if "rfs-config" not in parameters:
            parameters["rfs-config"] = json.dumps({"test": None})
            
        if "image-config" not in parameters:
            parameters["image-config"] = json.dumps({
                "reindex-from-snapshot": {
                    "image": "migrations/reindex_from_snapshot:latest",
                    "pull-policy": "IfNotPresent"
                },
                "migration-console": {
                    "image": "migrations/migration_console:latest", 
                    "pull-policy": "IfNotPresent"
                }
            })
            
        # Default to using localstack credentials
        parameters["use-localstack-aws-creds"] = parameters.get("use-localstack-aws-creds", True)
        parameters["localstack-enabled"] = parameters.get("localstack-enabled", "true")
            
        logger.debug("Workflow parameters prepared successfully")
        return parameters
        
    def start(self, *args, **kwargs) -> CommandResult:
        """
        Start the Argo workflow for document bulk loading.
        
        Returns:
            CommandResult: Result of the workflow creation operation
        """
        logger.info(f"Starting RFS backfill using Argo workflow template: {self.workflow_template_name}")
        
        # Get entrypoint from config or use default
        entrypoint = self.argo_config.get("entrypoint", "run-bulk-load")
        
        # Create workflow with the specified entrypoint
        workflow_options = {
            "entrypoint": entrypoint,
        }
        
        try:
            result = self.argo_service.start_workflow(
                workflow_template_name=self.workflow_template_name,
                parameters=self.parameters,
                workflow_options=workflow_options
            )
            
            if result.success:
                self.workflow_name = result.value
                logger.info(f"Successfully started Argo workflow: {self.workflow_name}")
                return CommandResult(True, f"Started RFS backfill workflow: {self.workflow_name}")
            else:
                logger.error(f"Failed to start Argo workflow: {result.value}")
                return CommandResult(False, f"Failed to start RFS backfill workflow: {result.value}")
        except Exception as e:
            logger.error(f"Exception while starting Argo workflow: {str(e)}", exc_info=True)
            return CommandResult(False, f"Exception while starting RFS backfill workflow: {str(e)}")

    def pause(self, *args, **kwargs) -> CommandResult:
        """Pause the Argo workflow by stopping it"""
        if not self.workflow_name:
            logger.warning("Cannot pause workflow: No active workflow found")
            return CommandResult(False, "No active workflow found to pause")
            
        workflow_name = str(self.workflow_name)  # Ensure it's a string
        logger.info(f"Pausing RFS backfill workflow: {workflow_name}")
        result = self.argo_service.stop_workflow(workflow_name=workflow_name)
        
        if result.success:
            logger.info(f"Successfully paused Argo workflow: {self.workflow_name}")
            return CommandResult(True, f"Paused RFS backfill workflow: {self.workflow_name}")
        else:
            error_msg = str(result.value) if result.value is not None else "Unknown error"
            logger.error(f"Failed to pause Argo workflow: {error_msg}")
            return CommandResult(False, f"Failed to pause RFS backfill workflow: {error_msg}")

    def stop(self, *args, **kwargs) -> CommandResult:
        """Stop the Argo workflow"""
        if not self.workflow_name:
            logger.warning("Cannot stop workflow: No active workflow found")
            return CommandResult(False, "No active workflow found to stop")
            
        workflow_name = str(self.workflow_name)  # Ensure it's a string
        logger.info(f"Stopping RFS backfill workflow: {workflow_name}")
        result = self.argo_service.stop_workflow(workflow_name=workflow_name)
        
        if result.success:
            logger.info(f"Successfully stopped Argo workflow: {self.workflow_name}")
            return CommandResult(True, f"Stopped RFS backfill workflow: {self.workflow_name}")
        else:
            error_msg = str(result.value) if result.value is not None else "Unknown error"
            logger.error(f"Failed to stop Argo workflow: {error_msg}")
            return CommandResult(False, f"Failed to stop RFS backfill workflow: {error_msg}")

    def scale(self, units: int, *args, **kwargs) -> CommandResult:
        """Scaling not directly supported for Argo workflows"""
        logger.warning("Scaling is not supported for Argo workflow-based RFS backfill")
        return CommandResult(False, "Scaling is not supported for Argo workflow-based RFS backfill")

    def archive(self, *args, archive_dir_path: str = None, archive_file_name: str = None, **kwargs) -> CommandResult:
        """Archive the working state index if the workflow is completed"""
        if not self.workflow_name:
            logger.warning("Cannot archive: No active workflow found")
            return CommandResult(False, "No active workflow found to archive")
            
        # Check if the workflow is in an ending state
        workflow_name = str(self.workflow_name)  # Ensure it's a string
        status_result = self.argo_service.get_workflow_status(workflow_name=workflow_name)
        if not status_result.success:
            error_msg = str(status_result.value) if status_result.value is not None else "Unknown error"
            logger.error(f"Failed to get workflow status: {error_msg}")
            return CommandResult(False, f"Failed to get workflow status: {error_msg}")
            
        status_info = status_result.value
        if not isinstance(status_info, dict):
            logger.error("Invalid status info returned: not a dictionary")
            return CommandResult(False, "Invalid status info returned from workflow")
            
        phase = status_info.get("phase", "")
        
        # Only archive if the workflow is completed
        if phase not in ENDING_ARGO_PHASES:
            logger.warning(f"Cannot archive: Workflow is still active with phase {phase}")
            return CommandResult(False, f"Cannot archive: Workflow is still active with phase {phase}")
        
        # Create a mock deployment status for the archive function
        mock_status = DeploymentStatus(0, 0, 0, 0)
        return perform_archive(
            target_cluster=self.target_cluster,
            deployment_status=mock_status,
            archive_dir_path=archive_dir_path,
            archive_file_name=archive_file_name
        )

    def get_status(self, deep_check=False, *args, **kwargs) -> CommandResult:
        """Get the status of the Argo workflow and the underlying RFS process"""
        if not self.workflow_name:
            logger.warning("Cannot get status: No active workflow found")
            return CommandResult(True, (BackfillStatus.STOPPED, "No active workflow found"))
            
        workflow_name = str(self.workflow_name)  # Ensure it's a string
        logger.info(f"Getting status of RFS backfill workflow: {workflow_name}")
        status_result = self.argo_service.get_workflow_status(workflow_name=workflow_name)
        
        if not status_result.success:
            error_msg = str(status_result.value) if status_result.value is not None else "Unknown error"
            logger.error(f"Failed to get workflow status: {error_msg}")
            return CommandResult(False, f"Failed to get workflow status: {error_msg}")
            
        status_info = status_result.value
        if not isinstance(status_info, dict):
            logger.error("Invalid status info returned: not a dictionary")
            return CommandResult(False, "Invalid status info returned from workflow")
            
        phase = status_info.get("phase", "")
        has_suspended_nodes = status_info.get("has_suspended_nodes", False)
        
        status_str = f"Workflow status: {phase}"
        if has_suspended_nodes:
            status_str += " (suspended)"
            
        if deep_check:
            try:
                session_name = self.parameters.get("session-name", "")
                shard_status = get_detailed_status(target_cluster=self.target_cluster, session_name=session_name)
                if shard_status:
                    status_str += f"\n{shard_status}"
            except Exception as e:
                logger.error(f"Failed to get detailed status: {e}")
        
        # Map Argo workflow phases to backfill status
        if phase in ["Running"]:
            if has_suspended_nodes:
                return CommandResult(True, (BackfillStatus.STOPPED, status_str))  # Use STOPPED for PAUSED
            return CommandResult(True, (BackfillStatus.RUNNING, status_str))
        elif phase in ["Pending"]:
            return CommandResult(True, (BackfillStatus.STARTING, status_str))
        elif phase in ["Succeeded"]:
            return CommandResult(True, (BackfillStatus.STOPPED, status_str))  # Use STOPPED for COMPLETED 
        elif phase in ["Failed", "Error"]:
            return CommandResult(True, (BackfillStatus.FAILED, status_str))
        elif phase in ["Stopped", "Terminated"]:
            return CommandResult(True, (BackfillStatus.STOPPED, status_str))
        else:
            return CommandResult(True, (BackfillStatus.NOT_STARTED, status_str))  # Use NOT_STARTED for UNKNOWN
            
    def build_backfill_status(self) -> BackfillOverallStatus:
        """Build detailed status information about the RFS backfill process"""
        active_workers = True
        
        if self.workflow_name:
            workflow_name = str(self.workflow_name)  # Ensure it's a string
            status_result = self.argo_service.get_workflow_status(workflow_name=workflow_name)
            if status_result.success and isinstance(status_result.value, dict):
                status_info = status_result.value
                phase = status_info.get("phase", "")
                
                # If workflow is in an ending state or suspended, workers are not active
                active_workers = (
                    phase not in ENDING_ARGO_PHASES and
                    not status_info.get("has_suspended_nodes", False)
                )
        
        # Get session name for detailed status
        session_name = self.parameters.get("session-name", "")
        return get_detailed_status_obj(self.target_cluster, active_workers, session_name)


class ECSRFSBackfill(RFSBackfill):
    def __init__(self, config: Dict, target_cluster: Cluster, client_options: Optional[ClientOptions] = None) -> None:
        super().__init__(config)
        self.client_options = client_options
        self.target_cluster = target_cluster
        self.default_scale = self.config["reindex_from_snapshot"].get("scale", 5)

        self.ecs_config = self.config["reindex_from_snapshot"]["ecs"]
        self.ecs_client = ECSService(cluster_name=self.ecs_config["cluster_name"],
                                     service_name=self.ecs_config["service_name"],
                                     aws_region=self.ecs_config.get("aws_region", None),
                                     client_options=self.client_options)

    def start(self, *args, **kwargs) -> CommandResult:
        logger.info(f"Starting RFS backfill by setting desired count to {self.default_scale} instances")
        return self.ecs_client.set_desired_count(self.default_scale)
    
    def pause(self, *args, **kwargs) -> CommandResult:
        logger.info("Pausing RFS backfill by setting desired count to 0 instances")
        return self.ecs_client.set_desired_count(0)

    def stop(self, *args, **kwargs) -> CommandResult:
        logger.info("Stopping RFS backfill by setting desired count to 0 instances")
        return self.ecs_client.set_desired_count(0)

    def scale(self, units: int, *args, **kwargs) -> CommandResult:
        logger.info(f"Scaling RFS backfill by setting desired count to {units} instances")
        return self.ecs_client.set_desired_count(units)
    
    def archive(self, *args, archive_dir_path: str = None, archive_file_name: str = None, **kwargs) -> CommandResult:
        status = self.ecs_client.get_instance_statuses()
        return perform_archive(target_cluster=self.target_cluster,
                               deployment_status=status,
                               archive_dir_path=archive_dir_path,
                               archive_file_name=archive_file_name)

    def get_status(self, deep_check=False, *args, **kwargs) -> CommandResult:
        logger.info(f"Getting status of RFS backfill, with {deep_check=}")
        instance_statuses = self.ecs_client.get_instance_statuses()
        if not instance_statuses:
            return CommandResult(False, "Failed to get instance statuses")

        status_string = str(instance_statuses)
        if deep_check:
            try:
                shard_status = get_detailed_status(target_cluster=self.target_cluster)
            except Exception as e:
                logger.error(f"Failed to get detailed status: {e}")
                shard_status = None
            if shard_status:
                status_string += f"\n{shard_status}"

        if instance_statuses.running > 0:
            return CommandResult(True, (BackfillStatus.RUNNING, status_string))
        elif instance_statuses.pending > 0:
            return CommandResult(True, (BackfillStatus.STARTING, status_string))
        return CommandResult(True, (BackfillStatus.STOPPED, status_string))
    
    def build_backfill_status(self) -> BackfillOverallStatus:
        deployment_status = self.ecs_client.get_instance_statuses()
        active_workers = True  # Assume there are active workers if we cannot lookup the deployment status
        if deployment_status is not None:
            active_workers = deployment_status.desired != 0

        return get_detailed_status_obj(self.target_cluster, active_workers)


def get_detailed_status(target_cluster: Cluster, session_name: Optional[str] = "") -> Optional[str]:
    values = get_detailed_status_obj(target_cluster,
                                     True,  # Assume active workers
                                     session_name)
    return "\n".join([f"Backfill {key}: {value}" for key, value in values.__dict__.items() if value is not None])


def _get_shard_setup_started_epoch(cluster, index_name: str) -> Optional[int]:
    """
    Try to read the special shard_setup doc and take its completedAt (epoch seconds) as 'started'.
    Returns None if not present.
    """
    try:
        resp = cluster.call_api(f"/{index_name}/_doc/shard_setup")
        body = resp.json()
        src = body.get("_source") or {}
        started_epoch = src.get("completedAt")
        if isinstance(started_epoch, (int, float)) and started_epoch > 0:
            return int(started_epoch)
    except requests.exceptions.RequestException as e:
        logger.debug(f"shard_setup doc not available: {e}")
    except Exception as e:
        logger.debug(f"Failed to parse shard_setup doc: {e}")
    return None


def _get_max_completed_epoch(cluster, index_name: str) -> Optional[int]:
    """
    Return the maximum completedAt (epoch seconds) across all docs.
    Only used once we've confirmed everything is completed.
    """
    body = {
        "size": 0,
        "aggs": {"max_completed": {"max": {"field": "completedAt"}}},
        "query": {"exists": {"field": "completedAt"}},
    }
    try:
        resp = cluster.call_api(
            f"/{index_name}/_search",
            data=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )
        aggs = resp.json().get("aggregations", {})
        val = aggs.get("max_completed", {}).get("value")
        if isinstance(val, (int, float)) and val > 0:
            return int(val)
    except requests.exceptions.RequestException as e:
        logger.debug(f"max completedAt aggregation failed: {e}")
    except Exception as e:
        logger.debug(f"Failed to parse max completedAt aggregation: {e}")
    return None


def _estimate_eta_ms_from_shards(started_epoch: Optional[int], pct: float) -> Optional[float]:
    """
    Simple ETA based on shard completion rate:
      remaining_time ~= elapsed * ((100 - pct) / pct)
    """
    if not started_epoch:
        return None
    if pct <= 0.0 or pct >= 100.0:
        return None
    now = datetime.now(timezone.utc).timestamp()
    elapsed_sec = max(now - started_epoch, 0.001)
    remaining_factor = (100.0 - pct) / pct
    return elapsed_sec * remaining_factor * 1000.0


@dataclass
class ShardStatusCounts:
    total: int = 0
    completed: int = 0
    incomplete: int = 0
    in_progress: int = 0
    unclaimed: int = 0


def get_detailed_status_obj(target_cluster: Cluster,
                            active_workers: bool = True,
                            session_name: Optional[str] = "") -> BackfillOverallStatus:
    # Check whether the working state index exists. If not, we can't run queries.
    index_suffix = f"_{session_name}" if session_name else ""
    index_to_check = f".migrations_working_state{index_suffix}"
    logger.info(f"Checking status for index: {index_to_check}")
    try:
        target_cluster.call_api("/" + index_to_check)
    except requests.exceptions.RequestException as e:
        logger.debug(f"Working state index does not yet exist, deep status checks can't be performed. {e}")
        raise DeepStatusNotYetAvailable

    total_key = "total"
    completed_key = "completed"
    incomplete_key = "incomplete"
    unclaimed_key = "unclaimed"
    in_progress_key = "in progress"

    queries = generate_status_queries()
    values = {key: parse_query_response(queries[key], target_cluster, index_to_check, key) for key in queries.keys()}
    if None in values.values():
        logger.warning(f"Failed to get values for some queries: {values}")

    import json
    logger.error(f"query response {json.dumps(values)}")

    counts = ShardStatusCounts(
        total=values.get(total_key, 0) or 0,
        completed=values.get(completed_key, 0) or 0,
        incomplete=values.get(incomplete_key, 0) or 0,
        in_progress=values.get(in_progress_key, 0) or 0,
        unclaimed=values.get(unclaimed_key, 0) or 0,
    )

    # started: read shard_setup.completedAt if available
    started_epoch = _get_shard_setup_started_epoch(target_cluster, index_to_check)
    started_iso = datetime.fromtimestamp(started_epoch, tz=timezone.utc).isoformat() if started_epoch else None

    # finished: only if everything is done, take max completedAt
    finished_iso, percentage_completed, eta_ms, status = compute_dervived_values(target_cluster,
                                                                                 index_to_check,
                                                                                 counts.total,
                                                                                 counts.completed,
                                                                                 started_epoch,
                                                                                 active_workers)

    return BackfillOverallStatus(
        status=status,
        percentage_completed=percentage_completed,
        eta_ms=eta_ms,
        started=started_iso,
        finished=finished_iso,
        shard_total=counts.total,
        shard_complete=counts.completed,
        shard_in_progress=counts.in_progress,
        shard_waiting=counts.unclaimed,
    )


def compute_dervived_values(target_cluster, index_to_check, total, completed, started_epoch, active_workers: bool):
    # Consider it completed if there's nothing to do (total = 0) or we've completed all shards
    if total == 0 or (total > 0 and completed >= total):
        max_completed_epoch = _get_max_completed_epoch(target_cluster, index_to_check)
        finished_iso = (
            datetime.fromtimestamp(max_completed_epoch, tz=timezone.utc).isoformat()
            if max_completed_epoch
            else datetime.now(timezone.utc).isoformat()
        )
        percentage_completed = 100.0
        eta_ms = None
        status = StepStateWithPause.COMPLETED
    else:
        finished_iso = None
        percentage_completed = (completed / total * 100.0) if total > 0 else 0.0
        if active_workers:
            eta_ms = _estimate_eta_ms_from_shards(started_epoch, percentage_completed)
            status = StepStateWithPause.RUNNING
        else:
            eta_ms = None
            status = StepStateWithPause.PAUSED
    return finished_iso, percentage_completed, eta_ms, status


EXTRACT_UNIQUE_INDEX_SHARD_SCRIPT = (
    "def id = doc['_id'].value;"
    "int a = id.indexOf('__');"
    "int b = id.indexOf('__', a + 2);"
    "if (a > -1 && b > -1) { return id.substring(0, a) + '__' + id.substring(a + 2, b); }"
)


def with_uniques(filter_query):
    return {
        "size": 0,
        "query": filter_query,
        "aggs": {
            "unique_pair_count": {"cardinality": {"script": {"lang": "painless", "source":
                                                             EXTRACT_UNIQUE_INDEX_SHARD_SCRIPT}}}
        },
    }


def generate_status_queries():
    current_epoch_seconds = int(datetime.now(timezone.utc).timestamp())
    total_query = with_uniques({"bool": {"must_not": [{"match": {"_id": "shard_setup"}},
                                                      {"exists": {"field": "successor_items"}}]}})
    complete_query = with_uniques({"bool": {"must": [{"exists": {"field": "completedAt"}}],
                                            "must_not": [{"match": {"_id": "shard_setup"}},
                                                         {"exists": {"field": "successor_items"}}]}})
    incomplete_query = with_uniques({"bool": {"must_not": [{"exists": {"field": "completedAt"}},
                                                           {"match": {"_id": "shard_setup"}}]}})
    in_progress_query = with_uniques({"bool": {"must": [
        {"range": {"expiration": {"gte": current_epoch_seconds}}},
        {"bool": {"must_not": [{"exists": {"field": "completedAt"}},
                               {"match": {"_id": "shard_setup"}}]}}
    ]}})
    unclaimed_query = with_uniques({"bool": {"must": [
        {"range": {"expiration": {"lt": current_epoch_seconds}}},
        {"bool": {"must_not": [{"exists": {"field": "completedAt"}},
                               {"match": {"_id": "shard_setup"}}]}}
    ]}})
    queries = {
        "total": total_query,
        "completed": complete_query,
        "incomplete": incomplete_query,
        "in progress": in_progress_query,
        "unclaimed": unclaimed_query
    }
    return queries


def all_shards_finished_processing(target_cluster: Cluster, session_name: Optional[str] = "") -> bool:
    d = get_detailed_status_obj(target_cluster, session_name=session_name)
    return d.shard_total == d.shard_complete and d.shard_in_progress == 0 and d.shard_waiting == 0


def perform_archive(target_cluster: Cluster,
                    deployment_status: DeploymentStatus,
                    archive_dir_path: Optional[str] = None,
                    archive_file_name: Optional[str] = None) -> CommandResult:
    logger.info("Confirming there are no currently in-progress workers")
    if deployment_status.running > 0 or deployment_status.pending > 0 or deployment_status.desired > 0:
        return CommandResult(False, RfsWorkersInProgress())

    try:
        backup_path = get_working_state_index_backup_path(archive_dir_path, archive_file_name)
        logger.info(f"Backing up working state index to {backup_path}")
        backup_working_state_index(target_cluster, WORKING_STATE_INDEX, backup_path)
        logger.info("Working state index backed up successful")

        logger.info("Cleaning up working state index on target cluster")
        target_cluster.call_api(
            f"/{WORKING_STATE_INDEX}",
            method=HttpMethod.DELETE,
            params={"ignore_unavailable": "true"}
        )
        logger.info("Working state index cleaned up successful")
        return CommandResult(True, backup_path)
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return CommandResult(False, WorkingIndexDoesntExist(WORKING_STATE_INDEX))
        return CommandResult(False, e)


def create_backfill(config: Dict, target_cluster: Cluster, client_options: Optional[ClientOptions] = None,
                    snapshot: Optional[Snapshot] = None) -> RFSBackfill:
    """
    Factory method to create an appropriate RFSBackfill implementation based on the configuration.
    
    Args:
        config: The RFS backfill configuration.
        target_cluster: The target cluster for the backfill.
        client_options: Optional client options.
        snapshot: Optional snapshot object for Argo implementation.
        
    Returns:
        An instance of RFSBackfill implementation.
        
    Raises:
        ValueError: If the configuration is invalid or no implementation is found.
    """
    if "reindex_from_snapshot" not in config:
        raise ValueError("Invalid config: missing 'reindex_from_snapshot' section")
        
    rfs_config = config["reindex_from_snapshot"]
    
    if "docker" in rfs_config and rfs_config["docker"] is not None:
        return DockerRFSBackfill(config, target_cluster)
    elif "ecs" in rfs_config and rfs_config["ecs"] is not None:
        return ECSRFSBackfill(config, target_cluster, client_options)
    elif "k8s" in rfs_config and rfs_config["k8s"] is not None:
        return K8sRFSBackfill(config, target_cluster, client_options)
    elif "argo" in rfs_config and rfs_config["argo"] is not None:
        return ArgoRFSBackfill(config, snapshot, target_cluster, client_options)
    else:
        raise ValueError("No valid RFS backfill implementation found in config")


def get_working_state_index_backup_path(archive_dir_path: Optional[str] = None, 
                                        archive_file_name: Optional[str] = None) -> str:
    # Get backup directory
    shared_logs_dir = os.getenv("SHARED_LOGS_DIR_PATH")
    if archive_dir_path:
        backup_dir = archive_dir_path
    elif shared_logs_dir is None:
        backup_dir = "./backfill_working_state"
    else:
        backup_dir = os.path.join(shared_logs_dir, "backfill_working_state")

    if archive_file_name:
        file_name = archive_file_name
    else:
        file_name = f"working_state_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    return os.path.join(backup_dir, file_name)


def backup_working_state_index(cluster: Cluster, index_name: str, backup_path: str):
    # Ensure the backup directory exists
    backup_dir = os.path.dirname(backup_path)
    os.makedirs(backup_dir, exist_ok=True)

    # Backup the docs in the working state index as a JSON array containing batches of documents
    with open(backup_path, 'w') as outfile:
        outfile.write("[\n")  # Start the JSON array
        first_batch = True

        for batch in cluster.fetch_all_documents(index_name=index_name):
            if not first_batch:
                outfile.write(",\n")
            else:
                first_batch = False
            
            # Dump the batch of documents as an entry in the array
            batch_json = json.dumps(batch, indent=4)
            outfile.write(batch_json)

        outfile.write("\n]")  # Close the JSON array


def parse_query_response(query: dict, cluster: Cluster, index_name: str, label: str) -> Optional[int]:
    try:
        logger.debug(f"Creating request: /{index_name}/_search; {query}")
        response = cluster.call_api(f"/{index_name}/_search", method=HttpMethod.POST, data=json.dumps(query),
                                    headers={'Content-Type': 'application/json'})
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        return None
    logger.debug(f"Query: {label}, {response.request.path_url}, {response.request.body}")
    body = response.json()
    logger.debug(f"Raw response: {body}")
    if "hits" in body:
        logger.debug(f"Hits on {label} query: {body['hits']}")
        logger.info(f"Sample of {label} shards: {[hit['_id'] for hit in body['hits']['hits']]}")
        return int(body['hits']['total']['value'])
    logger.warning(f"No hits on {label} query, migration_working_state index may not exist or be populated")
    return None
