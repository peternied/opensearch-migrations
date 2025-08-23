"""AWS ECS service management infrastructure."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from console_link.domain.exceptions.common_errors import InfrastructureError, ExternalServiceError

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """ECS Service status values."""
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    INACTIVE = "INACTIVE"


class DesiredStatus(Enum):
    """ECS Task desired status values."""
    RUNNING = "RUNNING"
    PENDING = "PENDING"
    STOPPED = "STOPPED"


@dataclass
class TaskInfo:
    """Information about an ECS task."""
    arn: str
    cluster_arn: str
    task_definition_arn: str
    desired_status: DesiredStatus
    last_status: str
    launch_type: str
    cpu: str
    memory: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    stopped_reason: Optional[str] = None
    group: Optional[str] = None


@dataclass
class ServiceInfo:
    """Information about an ECS service."""
    arn: str
    name: str
    cluster_arn: str
    status: ServiceStatus
    desired_count: int
    running_count: int
    pending_count: int
    task_definition: str
    launch_type: str
    deployment_configuration: Dict[str, Any]
    role_arn: Optional[str] = None


@dataclass
class ServiceDeploymentStatus:
    """Status of an ECS service deployment."""
    running: int
    pending: int
    desired: int
    failed: int = 0


class ECSError(InfrastructureError):
    """Raised when ECS operations fail."""
    pass


class ECSManagerInterface(ABC):
    """Abstract interface for ECS service management."""
    
    @abstractmethod
    def update_service_desired_count(self, cluster: str, service: str, desired_count: int) -> ServiceInfo:
        """Update the desired count for a service."""
        pass
    
    @abstractmethod
    def get_service_info(self, cluster: str, service: str) -> ServiceInfo:
        """Get information about a service."""
        pass
    
    @abstractmethod
    def get_service_deployment_status(self, cluster: str, service: str) -> ServiceDeploymentStatus:
        """Get deployment status of a service."""
        pass
    
    @abstractmethod
    def list_tasks(self, cluster: str, service: Optional[str] = None,
                   desired_status: Optional[DesiredStatus] = None) -> List[TaskInfo]:
        """List tasks in a cluster."""
        pass
    
    @abstractmethod
    def stop_task(self, cluster: str, task: str, reason: Optional[str] = None) -> TaskInfo:
        """Stop a task."""
        pass
    
    @abstractmethod
    def run_task(self, cluster: str, task_definition: str, count: int = 1,
                 launch_type: str = "EC2", **kwargs) -> List[TaskInfo]:
        """Run tasks from a task definition."""
        pass


class ECSManager(ECSManagerInterface):
    """Manage ECS services using the AWS boto3 client."""
    
    def __init__(self, region: Optional[str] = None, client_options: Optional[Dict[str, Any]] = None):
        """Initialize ECS manager.
        
        Args:
            region: AWS region
            client_options: Additional boto3 client options
        """
        try:
            from console_link.models.utils import create_boto3_client
            
            self.client = create_boto3_client(
                aws_service_name="ecs",
                region=region,
                client_options=client_options
            )
            self.region = region
            logger.info(f"Initialized ECS manager for region: {region or 'default'}")
            
        except ImportError:
            raise ECSError("boto3 not installed. Install with: pip install boto3")
        except Exception as e:
            raise ECSError(f"Failed to initialize ECS client: {e}")
    
    def update_service_desired_count(self, cluster: str, service: str, desired_count: int) -> ServiceInfo:
        """Update the desired count for a service.
        
        Args:
            cluster: Cluster name or ARN
            service: Service name or ARN
            desired_count: Desired number of tasks
            
        Returns:
            ServiceInfo object
            
        Raises:
            ECSError: If update fails
        """
        try:
            response = self.client.update_service(
                cluster=cluster,
                service=service,
                desiredCount=desired_count
            )
            
            self._check_response_errors(response)
            
            service_data = response['service']
            return self._parse_service_info(service_data)
            
        except Exception as e:
            raise ECSError(f"Failed to update service {cluster}/{service} desired count: {e}")
    
    def get_service_info(self, cluster: str, service: str) -> ServiceInfo:
        """Get information about a service.
        
        Args:
            cluster: Cluster name or ARN
            service: Service name or ARN
            
        Returns:
            ServiceInfo object
            
        Raises:
            ECSError: If service not found or query fails
        """
        try:
            response = self.client.describe_services(
                cluster=cluster,
                services=[service]
            )
            
            self._check_response_errors(response)
            
            if not response.get('services'):
                raise ECSError(f"Service {service} not found in cluster {cluster}")
            
            service_data = response['services'][0]
            return self._parse_service_info(service_data)
            
        except ECSError:
            raise
        except Exception as e:
            raise ECSError(f"Failed to get service info for {cluster}/{service}: {e}")
    
    def get_service_deployment_status(self, cluster: str, service: str) -> ServiceDeploymentStatus:
        """Get deployment status of a service.
        
        Args:
            cluster: Cluster name or ARN
            service: Service name or ARN
            
        Returns:
            ServiceDeploymentStatus object
            
        Raises:
            ECSError: If status cannot be retrieved
        """
        try:
            service_info = self.get_service_info(cluster, service)
            
            # Get failed task count
            failed_count = 0
            response = self.client.describe_tasks(
                cluster=cluster,
                tasks=[]  # Empty list gets all tasks
            )
            
            if response.get('failures'):
                failed_count = len(response['failures'])
            
            return ServiceDeploymentStatus(
                running=service_info.running_count,
                pending=service_info.pending_count,
                desired=service_info.desired_count,
                failed=failed_count
            )
            
        except ECSError:
            raise
        except Exception as e:
            raise ECSError(f"Failed to get deployment status for {cluster}/{service}: {e}")
    
    def list_tasks(self, cluster: str, service: Optional[str] = None,
                   desired_status: Optional[DesiredStatus] = None) -> List[TaskInfo]:
        """List tasks in a cluster.
        
        Args:
            cluster: Cluster name or ARN
            service: Optional service name to filter by
            desired_status: Optional desired status to filter by
            
        Returns:
            List of TaskInfo objects
            
        Raises:
            ECSError: If listing fails
        """
        try:
            # List task ARNs
            list_params = {"cluster": cluster}
            if service:
                list_params["serviceName"] = service
            if desired_status:
                list_params["desiredStatus"] = desired_status.value
            
            response = self.client.list_tasks(**list_params)
            self._check_response_errors(response)
            
            task_arns = response.get('taskArns', [])
            if not task_arns:
                return []
            
            # Describe tasks
            describe_response = self.client.describe_tasks(
                cluster=cluster,
                tasks=task_arns
            )
            self._check_response_errors(describe_response)
            
            tasks = []
            for task_data in describe_response.get('tasks', []):
                tasks.append(self._parse_task_info(task_data))
            
            return tasks
            
        except Exception as e:
            raise ECSError(f"Failed to list tasks in cluster {cluster}: {e}")
    
    def stop_task(self, cluster: str, task: str, reason: Optional[str] = None) -> TaskInfo:
        """Stop a task.
        
        Args:
            cluster: Cluster name or ARN
            task: Task ID or ARN
            reason: Optional reason for stopping
            
        Returns:
            TaskInfo object
            
        Raises:
            ECSError: If stopping fails
        """
        try:
            params = {"cluster": cluster, "task": task}
            if reason:
                params["reason"] = reason
            
            response = self.client.stop_task(**params)
            self._check_response_errors(response)
            
            task_data = response.get('task', {})
            return self._parse_task_info(task_data)
            
        except Exception as e:
            raise ECSError(f"Failed to stop task {task} in cluster {cluster}: {e}")
    
    def run_task(self, cluster: str, task_definition: str, count: int = 1,
                 launch_type: str = "EC2", **kwargs) -> List[TaskInfo]:
        """Run tasks from a task definition.
        
        Args:
            cluster: Cluster name or ARN
            task_definition: Task definition family:revision or ARN
            count: Number of tasks to run
            launch_type: Launch type (EC2, FARGATE)
            **kwargs: Additional run_task parameters
            
        Returns:
            List of TaskInfo objects for started tasks
            
        Raises:
            ECSError: If task start fails
        """
        try:
            params = {
                "cluster": cluster,
                "taskDefinition": task_definition,
                "count": count,
                "launchType": launch_type
            }
            params.update(kwargs)
            
            response = self.client.run_task(**params)
            self._check_response_errors(response)
            
            tasks = []
            for task_data in response.get('tasks', []):
                tasks.append(self._parse_task_info(task_data))
            
            if response.get('failures'):
                failure_reasons = [f"{f.get('arn', 'unknown')}: {f.get('reason', 'unknown reason')}" 
                                 for f in response['failures']]
                logger.warning(f"Some tasks failed to start: {', '.join(failure_reasons)}")
            
            return tasks
            
        except Exception as e:
            raise ECSError(f"Failed to run tasks from {task_definition}: {e}")
    
    def _check_response_errors(self, response: Dict[str, Any]) -> None:
        """Check AWS API response for errors.
        
        Args:
            response: AWS API response
            
        Raises:
            ExternalServiceError: If AWS returned an error
        """
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') not in [200, 201]:
            error_code = response.get('Error', {}).get('Code', 'Unknown')
            error_message = response.get('Error', {}).get('Message', 'Unknown error')
            raise ExternalServiceError(f"AWS API error {error_code}: {error_message}")
    
    def _parse_service_info(self, service_data: Dict[str, Any]) -> ServiceInfo:
        """Parse service data from AWS API response.
        
        Args:
            service_data: Service data from AWS API
            
        Returns:
            ServiceInfo object
        """
        try:
            status = ServiceStatus(service_data.get('status', 'INACTIVE'))
        except ValueError:
            status = ServiceStatus.INACTIVE
        
        return ServiceInfo(
            arn=service_data.get('serviceArn', ''),
            name=service_data.get('serviceName', ''),
            cluster_arn=service_data.get('clusterArn', ''),
            status=status,
            desired_count=service_data.get('desiredCount', 0),
            running_count=service_data.get('runningCount', 0),
            pending_count=service_data.get('pendingCount', 0),
            task_definition=service_data.get('taskDefinition', ''),
            launch_type=service_data.get('launchType', 'EC2'),
            deployment_configuration=service_data.get('deploymentConfiguration', {}),
            role_arn=service_data.get('roleArn')
        )
    
    def _parse_task_info(self, task_data: Dict[str, Any]) -> TaskInfo:
        """Parse task data from AWS API response.
        
        Args:
            task_data: Task data from AWS API
            
        Returns:
            TaskInfo object
        """
        try:
            desired_status = DesiredStatus(task_data.get('desiredStatus', 'STOPPED'))
        except ValueError:
            desired_status = DesiredStatus.STOPPED
        
        return TaskInfo(
            arn=task_data.get('taskArn', ''),
            cluster_arn=task_data.get('clusterArn', ''),
            task_definition_arn=task_data.get('taskDefinitionArn', ''),
            desired_status=desired_status,
            last_status=task_data.get('lastStatus', ''),
            launch_type=task_data.get('launchType', 'EC2'),
            cpu=task_data.get('cpu', '0'),
            memory=task_data.get('memory', '0'),
            started_at=task_data.get('startedAt'),
            stopped_at=task_data.get('stoppedAt'),
            stopped_reason=task_data.get('stoppedReason'),
            group=task_data.get('group')
        )


class MockECSManager(ECSManagerInterface):
    """Mock ECS manager for testing."""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_counter = 0
    
    def update_service_desired_count(self, cluster: str, service: str, desired_count: int) -> ServiceInfo:
        """Mock update service desired count."""
        key = f"{cluster}/{service}"
        if key not in self.services:
            # Create default service
            self.services[key] = ServiceInfo(
                arn=f"arn:aws:ecs:us-east-1:123456789012:service/{cluster}/{service}",
                name=service,
                cluster_arn=f"arn:aws:ecs:us-east-1:123456789012:cluster/{cluster}",
                status=ServiceStatus.ACTIVE,
                desired_count=0,
                running_count=0,
                pending_count=0,
                task_definition="mock-task-def:1",
                launch_type="EC2",
                deployment_configuration={}
            )
        
        self.services[key].desired_count = desired_count
        self.services[key].pending_count = max(0, desired_count - self.services[key].running_count)
        logger.info(f"Mock: Updated service {key} desired count to {desired_count}")
        
        return self.services[key]
    
    def get_service_info(self, cluster: str, service: str) -> ServiceInfo:
        """Mock get service info."""
        key = f"{cluster}/{service}"
        if key not in self.services:
            raise ECSError(f"Service {key} not found")
        return self.services[key]
    
    def get_service_deployment_status(self, cluster: str, service: str) -> ServiceDeploymentStatus:
        """Mock get deployment status."""
        service_info = self.get_service_info(cluster, service)
        return ServiceDeploymentStatus(
            running=service_info.running_count,
            pending=service_info.pending_count,
            desired=service_info.desired_count,
            failed=0
        )
    
    def list_tasks(self, cluster: str, service: Optional[str] = None,
                   desired_status: Optional[DesiredStatus] = None) -> List[TaskInfo]:
        """Mock list tasks."""
        tasks = []
        for task_key, task in self.tasks.items():
            if cluster not in task.cluster_arn:
                continue
            if service and service not in task.group:
                continue
            if desired_status and task.desired_status != desired_status:
                continue
            tasks.append(task)
        return tasks
    
    def stop_task(self, cluster: str, task: str, reason: Optional[str] = None) -> TaskInfo:
        """Mock stop task."""
        if task not in self.tasks:
            raise ECSError(f"Task {task} not found")
        
        self.tasks[task].desired_status = DesiredStatus.STOPPED
        self.tasks[task].stopped_reason = reason or "Stopped by user"
        logger.info(f"Mock: Stopped task {task}")
        
        return self.tasks[task]
    
    def run_task(self, cluster: str, task_definition: str, count: int = 1,
                 launch_type: str = "EC2", **kwargs) -> List[TaskInfo]:
        """Mock run task."""
        tasks = []
        for i in range(count):
            self.task_counter += 1
            task_id = f"mock-task-{self.task_counter}"
            task = TaskInfo(
                arn=f"arn:aws:ecs:us-east-1:123456789012:task/{cluster}/{task_id}",
                cluster_arn=f"arn:aws:ecs:us-east-1:123456789012:cluster/{cluster}",
                task_definition_arn=task_definition,
                desired_status=DesiredStatus.RUNNING,
                last_status="PENDING",
                launch_type=launch_type,
                cpu="256",
                memory="512",
                group=kwargs.get('group')
            )
            self.tasks[task_id] = task
            tasks.append(task)
        
        logger.info(f"Mock: Started {count} tasks from {task_definition}")
        return tasks
