"""Kubernetes deployment management infrastructure."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from console_link.domain.exceptions.common_errors import InfrastructureError

logger = logging.getLogger(__name__)


class PodPhase(Enum):
    """Kubernetes pod phases."""
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


@dataclass
class PodInfo:
    """Information about a Kubernetes pod."""
    name: str
    namespace: str
    phase: PodPhase
    ready: bool
    node_name: Optional[str]
    labels: Dict[str, str]
    deletion_timestamp: Optional[str] = None


@dataclass
class DeploymentInfo:
    """Information about a Kubernetes deployment."""
    name: str
    namespace: str
    replicas: int
    ready_replicas: int
    available_replicas: int
    unavailable_replicas: int
    labels: Dict[str, str]
    selector: Dict[str, str]


@dataclass
class DeploymentStatus:
    """Status of a Kubernetes deployment."""
    running: int
    pending: int
    desired: int
    terminating: int
    available: int
    ready: int


class KubernetesError(InfrastructureError):
    """Raised when Kubernetes operations fail."""
    pass


class K8sManagerInterface(ABC):
    """Abstract interface for Kubernetes deployment management."""
    
    @abstractmethod
    def scale_deployment(self, name: str, namespace: str, replicas: int) -> None:
        """Scale a deployment to specified replicas."""
        pass
    
    @abstractmethod
    def get_deployment_info(self, name: str, namespace: str) -> DeploymentInfo:
        """Get information about a deployment."""
        pass
    
    @abstractmethod
    def get_deployment_status(self, name: str, namespace: str) -> DeploymentStatus:
        """Get status of a deployment."""
        pass
    
    @abstractmethod
    def list_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[PodInfo]:
        """List pods in a namespace."""
        pass
    
    @abstractmethod
    def delete_pod(self, name: str, namespace: str, grace_period: Optional[int] = None) -> None:
        """Delete a pod."""
        pass
    
    @abstractmethod
    def exec_in_pod(self, name: str, namespace: str, command: List[str],
                    container: Optional[str] = None, stdin: bool = False,
                    stdout: bool = True, stderr: bool = True) -> str:
        """Execute command in a pod."""
        pass


class K8sManager(K8sManagerInterface):
    """Manage Kubernetes deployments using the Kubernetes Python client."""
    
    def __init__(self, in_cluster: bool = True, kubeconfig_path: Optional[str] = None):
        """Initialize K8s manager.
        
        Args:
            in_cluster: Whether running inside a Kubernetes cluster
            kubeconfig_path: Path to kubeconfig file (if not in-cluster)
        """
        try:
            from kubernetes import client, config
            
            if in_cluster:
                try:
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster Kubernetes configuration")
                except config.ConfigException:
                    logger.warning("Unable to load in-cluster config, falling back to kubeconfig")
                    config.load_kube_config(config_file=kubeconfig_path)
            else:
                config.load_kube_config(config_file=kubeconfig_path)
                logger.info(f"Loaded kubeconfig from: {kubeconfig_path or 'default location'}")
            
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            
        except ImportError:
            raise KubernetesError("Kubernetes Python client not installed. Install with: pip install kubernetes")
        except Exception as e:
            raise KubernetesError(f"Failed to initialize Kubernetes client: {e}")
    
    def scale_deployment(self, name: str, namespace: str, replicas: int) -> None:
        """Scale a deployment to specified replicas.
        
        Args:
            name: Deployment name
            namespace: Namespace
            replicas: Desired number of replicas
            
        Raises:
            KubernetesError: If scaling fails
        """
        try:
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment_scale(
                name=name,
                namespace=namespace,
                body=body
            )
            logger.info(f"Scaled deployment {namespace}/{name} to {replicas} replicas")
        except Exception as e:
            raise KubernetesError(f"Failed to scale deployment {namespace}/{name}: {e}")
    
    def get_deployment_info(self, name: str, namespace: str) -> DeploymentInfo:
        """Get information about a deployment.
        
        Args:
            name: Deployment name
            namespace: Namespace
            
        Returns:
            DeploymentInfo object
            
        Raises:
            KubernetesError: If deployment not found or query fails
        """
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            return DeploymentInfo(
                name=deployment.metadata.name,
                namespace=deployment.metadata.namespace,
                replicas=deployment.spec.replicas or 0,
                ready_replicas=deployment.status.ready_replicas or 0,
                available_replicas=deployment.status.available_replicas or 0,
                unavailable_replicas=deployment.status.unavailable_replicas or 0,
                labels=deployment.metadata.labels or {},
                selector=deployment.spec.selector.match_labels or {}
            )
            
        except Exception as e:
            raise KubernetesError(f"Failed to get deployment info for {namespace}/{name}: {e}")
    
    def get_deployment_status(self, name: str, namespace: str) -> DeploymentStatus:
        """Get status of a deployment.
        
        Args:
            name: Deployment name
            namespace: Namespace
            
        Returns:
            DeploymentStatus object
            
        Raises:
            KubernetesError: If status cannot be retrieved
        """
        try:
            # Get deployment info
            deployment_info = self.get_deployment_info(name, namespace)
            
            # Get pods for this deployment
            label_selector = ",".join([f"{k}={v}" for k, v in deployment_info.selector.items()])
            pods = self.list_pods(namespace, label_selector)
            
            # Count pod states
            running = 0
            pending = 0
            terminating = 0
            
            for pod in pods:
                if pod.deletion_timestamp:
                    terminating += 1
                elif pod.phase == PodPhase.RUNNING:
                    running += 1
                elif pod.phase == PodPhase.PENDING:
                    pending += 1
            
            return DeploymentStatus(
                running=running,
                pending=pending,
                desired=deployment_info.replicas,
                terminating=terminating,
                available=deployment_info.available_replicas,
                ready=deployment_info.ready_replicas
            )
            
        except KubernetesError:
            raise
        except Exception as e:
            raise KubernetesError(f"Failed to get deployment status for {namespace}/{name}: {e}")
    
    def list_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[PodInfo]:
        """List pods in a namespace.
        
        Args:
            namespace: Namespace to list pods from
            label_selector: Optional label selector (e.g., "app=myapp,env=prod")
            
        Returns:
            List of PodInfo objects
            
        Raises:
            KubernetesError: If listing fails
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            pod_list = []
            for pod in pods.items:
                # Determine pod phase
                try:
                    phase = PodPhase(pod.status.phase)
                except ValueError:
                    phase = PodPhase.UNKNOWN
                
                # Check if pod is ready
                ready = False
                if pod.status.conditions:
                    for condition in pod.status.conditions:
                        if condition.type == "Ready" and condition.status == "True":
                            ready = True
                            break
                
                pod_list.append(PodInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    phase=phase,
                    ready=ready,
                    node_name=pod.spec.node_name,
                    labels=pod.metadata.labels or {},
                    deletion_timestamp=pod.metadata.deletion_timestamp
                ))
            
            return pod_list
            
        except Exception as e:
            raise KubernetesError(f"Failed to list pods in namespace {namespace}: {e}")
    
    def delete_pod(self, name: str, namespace: str, grace_period: Optional[int] = None) -> None:
        """Delete a pod.
        
        Args:
            name: Pod name
            namespace: Namespace
            grace_period: Grace period in seconds
            
        Raises:
            KubernetesError: If deletion fails
        """
        try:
            body = None
            if grace_period is not None:
                from kubernetes import client as k8s_client
                body = k8s_client.V1DeleteOptions(grace_period_seconds=grace_period)
            
            self.core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
                body=body
            )
            logger.info(f"Deleted pod {namespace}/{name}")
        except Exception as e:
            raise KubernetesError(f"Failed to delete pod {namespace}/{name}: {e}")
    
    def exec_in_pod(self, name: str, namespace: str, command: List[str],
                    container: Optional[str] = None, stdin: bool = False,
                    stdout: bool = True, stderr: bool = True) -> str:
        """Execute command in a pod.
        
        Args:
            name: Pod name
            namespace: Namespace
            command: Command to execute
            container: Container name (if multiple containers)
            stdin: Attach stdin
            stdout: Attach stdout
            stderr: Attach stderr
            
        Returns:
            Command output
            
        Raises:
            KubernetesError: If execution fails
        """
        try:
            from kubernetes.stream import stream
            
            # Execute command
            exec_command = ["/bin/sh", "-c", " ".join(command)] if len(command) > 1 else command
            
            resp = stream(
                self.core_v1.connect_get_namespaced_pod_exec,
                name,
                namespace,
                command=exec_command,
                container=container,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                tty=False
            )
            
            return resp
            
        except Exception as e:
            raise KubernetesError(f"Failed to execute command in pod {namespace}/{name}: {e}")


class MockK8sManager(K8sManagerInterface):
    """Mock Kubernetes manager for testing."""
    
    def __init__(self):
        self.deployments: Dict[str, DeploymentInfo] = {}
        self.pods: Dict[str, PodInfo] = {}
        self.executed_commands: List[Dict[str, Any]] = []
    
    def scale_deployment(self, name: str, namespace: str, replicas: int) -> None:
        """Mock scale deployment."""
        key = f"{namespace}/{name}"
        if key in self.deployments:
            self.deployments[key].replicas = replicas
            logger.info(f"Mock: Scaled deployment {key} to {replicas} replicas")
        else:
            raise KubernetesError(f"Deployment {key} not found")
    
    def get_deployment_info(self, name: str, namespace: str) -> DeploymentInfo:
        """Mock get deployment info."""
        key = f"{namespace}/{name}"
        if key in self.deployments:
            return self.deployments[key]
        
        # Create default deployment
        deployment = DeploymentInfo(
            name=name,
            namespace=namespace,
            replicas=1,
            ready_replicas=1,
            available_replicas=1,
            unavailable_replicas=0,
            labels={"app": name},
            selector={"app": name}
        )
        self.deployments[key] = deployment
        return deployment
    
    def get_deployment_status(self, name: str, namespace: str) -> DeploymentStatus:
        """Mock get deployment status."""
        deployment = self.get_deployment_info(name, namespace)
        
        # Count mock pods
        running = 0
        pending = 0
        terminating = 0
        
        for pod_key, pod in self.pods.items():
            if pod.namespace == namespace and pod.labels.get("app") == name:
                if pod.deletion_timestamp:
                    terminating += 1
                elif pod.phase == PodPhase.RUNNING:
                    running += 1
                elif pod.phase == PodPhase.PENDING:
                    pending += 1
        
        return DeploymentStatus(
            running=running,
            pending=pending,
            desired=deployment.replicas,
            terminating=terminating,
            available=deployment.available_replicas,
            ready=deployment.ready_replicas
        )
    
    def list_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[PodInfo]:
        """Mock list pods."""
        pods = []
        for pod in self.pods.values():
            if pod.namespace != namespace:
                continue
            
            # Simple label selector matching
            if label_selector:
                matches = True
                for selector in label_selector.split(","):
                    if "=" in selector:
                        key, value = selector.split("=", 1)
                        if pod.labels.get(key) != value:
                            matches = False
                            break
                if not matches:
                    continue
            
            pods.append(pod)
        
        return pods
    
    def delete_pod(self, name: str, namespace: str, grace_period: Optional[int] = None) -> None:
        """Mock delete pod."""
        key = f"{namespace}/{name}"
        if key in self.pods:
            del self.pods[key]
            logger.info(f"Mock: Deleted pod {key}")
        else:
            raise KubernetesError(f"Pod {key} not found")
    
    def exec_in_pod(self, name: str, namespace: str, command: List[str], **kwargs) -> str:
        """Mock exec in pod."""
        self.executed_commands.append({
            "pod": f"{namespace}/{name}",
            "command": command,
            "kwargs": kwargs
        })
        return "Mock execution output"
