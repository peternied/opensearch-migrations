"""Docker container management infrastructure."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from console_link.domain.exceptions.common_errors import InfrastructureError
from console_link.infrastructure.command_executor import (
    CommandExecutor, 
    CommandExecutorInterface,
    CommandExecutionError,
    OutputMode
)

logger = logging.getLogger(__name__)


@dataclass
class ContainerInfo:
    """Information about a Docker container."""
    id: str
    name: str
    status: str
    image: str
    ports: Dict[str, str]
    labels: Dict[str, str]


class DockerError(InfrastructureError):
    """Raised when Docker operations fail."""
    pass


class DockerManagerInterface(ABC):
    """Abstract interface for Docker container management."""
    
    @abstractmethod
    def run_container(self, image: str, name: Optional[str] = None,
                     command: Optional[List[str]] = None,
                     environment: Optional[Dict[str, str]] = None,
                     volumes: Optional[Dict[str, str]] = None,
                     ports: Optional[Dict[str, str]] = None,
                     network: Optional[str] = None,
                     detached: bool = True,
                     **kwargs) -> str:
        """Run a Docker container."""
        pass
    
    @abstractmethod
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container."""
        pass
    
    @abstractmethod
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container."""
        pass
    
    @abstractmethod
    def get_container_info(self, container_id: str) -> ContainerInfo:
        """Get information about a container."""
        pass
    
    @abstractmethod
    def list_containers(self, all_containers: bool = False, labels: Optional[Dict[str, str]] = None) -> List[ContainerInfo]:
        """List containers."""
        pass
    
    @abstractmethod
    def execute_in_container(self, container_id: str, command: List[str],
                           user: Optional[str] = None,
                           workdir: Optional[str] = None) -> str:
        """Execute a command inside a running container."""
        pass


class DockerManager(DockerManagerInterface):
    """Manage Docker containers using the Docker CLI."""
    
    def __init__(self, command_executor: Optional[CommandExecutorInterface] = None):
        """Initialize Docker manager.
        
        Args:
            command_executor: Command executor to use (defaults to CommandExecutor)
        """
        self.executor = command_executor or CommandExecutor()
    
    def run_container(self, image: str, name: Optional[str] = None,
                     command: Optional[List[str]] = None,
                     environment: Optional[Dict[str, str]] = None,
                     volumes: Optional[Dict[str, str]] = None,
                     ports: Optional[Dict[str, str]] = None,
                     network: Optional[str] = None,
                     detached: bool = True,
                     remove: bool = False,
                     labels: Optional[Dict[str, str]] = None,
                     **kwargs) -> str:
        """Run a Docker container.
        
        Args:
            image: Docker image to run
            name: Container name
            command: Command to run in container
            environment: Environment variables
            volumes: Volume mappings (host:container)
            ports: Port mappings (host:container)
            network: Network to connect to
            detached: Run in detached mode
            remove: Auto-remove container when it exits
            labels: Labels to add to container
            **kwargs: Additional docker run arguments
            
        Returns:
            Container ID
            
        Raises:
            DockerError: If container fails to start
        """
        docker_cmd = ["docker", "run"]
        
        if detached:
            docker_cmd.append("-d")
        
        if remove:
            docker_cmd.append("--rm")
            
        if name:
            docker_cmd.extend(["--name", name])
        
        if network:
            docker_cmd.extend(["--network", network])
        
        # Add environment variables
        if environment:
            for key, value in environment.items():
                docker_cmd.extend(["-e", f"{key}={value}"])
        
        # Add volumes
        if volumes:
            for host_path, container_path in volumes.items():
                docker_cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        # Add ports
        if ports:
            for host_port, container_port in ports.items():
                docker_cmd.extend(["-p", f"{host_port}:{container_port}"])
        
        # Add labels
        if labels:
            for key, value in labels.items():
                docker_cmd.extend(["--label", f"{key}={value}"])
        
        # Add any additional arguments
        for key, value in kwargs.items():
            if isinstance(value, bool) and value:
                docker_cmd.append(f"--{key.replace('_', '-')}")
            elif value is not None:
                docker_cmd.extend([f"--{key.replace('_', '-')}", str(value)])
        
        # Add image
        docker_cmd.append(image)
        
        # Add command if provided
        if command:
            docker_cmd.extend(command)
        
        try:
            result = self.executor.execute(docker_cmd, mode=OutputMode.CAPTURE)
            container_id = (result.stdout or "").strip()
            if not container_id:
                raise DockerError("Container started but no ID returned")
            logger.info(f"Started container {container_id[:12]} from image {image}")
            return container_id
        except CommandExecutionError as e:
            raise DockerError(f"Failed to run container: {e}")
    
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container.
        
        Args:
            container_id: Container ID or name
            timeout: Seconds to wait before killing
            
        Raises:
            DockerError: If container fails to stop
        """
        try:
            self.executor.execute(
                ["docker", "stop", "-t", str(timeout), container_id],
                mode=OutputMode.QUIET
            )
            logger.info(f"Stopped container {container_id[:12]}")
        except CommandExecutionError as e:
            raise DockerError(f"Failed to stop container {container_id}: {e}")
    
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container.
        
        Args:
            container_id: Container ID or name
            force: Force removal of running container
            
        Raises:
            DockerError: If container fails to be removed
        """
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)
        
        try:
            self.executor.execute(cmd, mode=OutputMode.QUIET)
            logger.info(f"Removed container {container_id[:12]}")
        except CommandExecutionError as e:
            raise DockerError(f"Failed to remove container {container_id}: {e}")
    
    def get_container_info(self, container_id: str) -> ContainerInfo:
        """Get information about a container.
        
        Args:
            container_id: Container ID or name
            
        Returns:
            ContainerInfo object
            
        Raises:
            DockerError: If container not found or inspection fails
        """
        try:
            # Get container details using docker inspect
            result = self.executor.execute(
                ["docker", "inspect", "--format", 
                 "{{.Id}}|{{.Name}}|{{.State.Status}}|{{.Config.Image}}", 
                 container_id],
                mode=OutputMode.CAPTURE
            )
            
            output = (result.stdout or "").strip()
            if not output:
                raise DockerError(f"No output from docker inspect")
            
            parts = output.split("|")
            if len(parts) != 4:
                raise DockerError(f"Unexpected inspect output format")
            
            # Get ports
            port_result = self.executor.execute(
                ["docker", "port", container_id],
                mode=OutputMode.CAPTURE
            )
            ports = self._parse_port_output(port_result.stdout or "")
            
            # Get labels
            label_result = self.executor.execute(
                ["docker", "inspect", "--format", "{{json .Config.Labels}}", container_id],
                mode=OutputMode.CAPTURE
            )
            
            import json
            labels = json.loads((label_result.stdout or "{}").strip()) or {}
            
            return ContainerInfo(
                id=parts[0],
                name=parts[1].lstrip("/"),  # Remove leading slash
                status=parts[2],
                image=parts[3],
                ports=ports,
                labels=labels
            )
            
        except CommandExecutionError as e:
            raise DockerError(f"Failed to get container info for {container_id}: {e}")
        except Exception as e:
            raise DockerError(f"Error parsing container info: {e}")
    
    def list_containers(self, all_containers: bool = False, labels: Optional[Dict[str, str]] = None) -> List[ContainerInfo]:
        """List containers.
        
        Args:
            all_containers: Include stopped containers
            labels: Filter by labels
            
        Returns:
            List of ContainerInfo objects
            
        Raises:
            DockerError: If listing fails
        """
        cmd = ["docker", "ps", "--format", 
               "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"]
        
        if all_containers:
            cmd.append("-a")
        
        if labels:
            for key, value in labels.items():
                cmd.extend(["--filter", f"label={key}={value}"])
        
        try:
            result = self.executor.execute(cmd, mode=OutputMode.CAPTURE)
            containers = []
            
            output = (result.stdout or "").strip()
            if not output:
                return containers
                
            for line in output.split("\n"):
                if not line:
                    continue
                    
                parts = line.split("|")
                if len(parts) == 4:
                    # For list operations, we don't fetch full details
                    containers.append(ContainerInfo(
                        id=parts[0],
                        name=parts[1],
                        status=parts[2],
                        image=parts[3],
                        ports={},
                        labels={}
                    ))
            
            return containers
            
        except CommandExecutionError as e:
            raise DockerError(f"Failed to list containers: {e}")
    
    def execute_in_container(self, container_id: str, command: List[str],
                           user: Optional[str] = None,
                           workdir: Optional[str] = None,
                           interactive: bool = False) -> str:
        """Execute a command inside a running container.
        
        Args:
            container_id: Container ID or name
            command: Command to execute
            user: User to run command as
            workdir: Working directory
            interactive: Run interactively
            
        Returns:
            Command output
            
        Raises:
            DockerError: If execution fails
        """
        docker_cmd = ["docker", "exec"]
        
        if interactive:
            docker_cmd.extend(["-i", "-t"])
            
        if user:
            docker_cmd.extend(["-u", user])
            
        if workdir:
            docker_cmd.extend(["-w", workdir])
        
        docker_cmd.append(container_id)
        docker_cmd.extend(command)
        
        try:
            mode = OutputMode.STREAM if interactive else OutputMode.CAPTURE
            result = self.executor.execute(docker_cmd, mode=mode, print_output=interactive)
            return result.stdout or ""
        except CommandExecutionError as e:
            raise DockerError(f"Failed to execute command in container {container_id}: {e}")
    
    def _parse_port_output(self, output: str) -> Dict[str, str]:
        """Parse docker port command output.
        
        Args:
            output: Output from docker port command
            
        Returns:
            Dictionary of container_port: host_binding
        """
        ports = {}
        for line in output.strip().split("\n"):
            if " -> " in line:
                container_port, host_binding = line.split(" -> ")
                ports[container_port] = host_binding
        return ports


class MockDockerManager(DockerManagerInterface):
    """Mock Docker manager for testing."""
    
    def __init__(self):
        self.containers: Dict[str, ContainerInfo] = {}
        self.next_id = 1
        self.executed_commands: List[Dict[str, Any]] = []
    
    def run_container(self, image: str, name: Optional[str] = None, **kwargs) -> str:
        """Mock container run."""
        container_id = f"mock-container-{self.next_id}"
        self.next_id += 1
        
        self.containers[container_id] = ContainerInfo(
            id=container_id,
            name=name or container_id,
            status="running",
            image=image,
            ports=kwargs.get("ports", {}),
            labels=kwargs.get("labels", {})
        )
        
        return container_id
    
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Mock container stop."""
        if container_id in self.containers:
            self.containers[container_id].status = "exited"
    
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Mock container removal."""
        if container_id in self.containers:
            del self.containers[container_id]
        elif not force:
            raise DockerError(f"Container {container_id} not found")
    
    def get_container_info(self, container_id: str) -> ContainerInfo:
        """Mock get container info."""
        if container_id not in self.containers:
            raise DockerError(f"Container {container_id} not found")
        return self.containers[container_id]
    
    def list_containers(self, all_containers: bool = False, labels: Optional[Dict[str, str]] = None) -> List[ContainerInfo]:
        """Mock list containers."""
        containers = list(self.containers.values())
        
        if not all_containers:
            containers = [c for c in containers if c.status == "running"]
        
        if labels:
            containers = [c for c in containers if all(
                c.labels.get(k) == v for k, v in labels.items()
            )]
        
        return containers
    
    def execute_in_container(self, container_id: str, command: List[str], **kwargs) -> str:
        """Mock command execution."""
        self.executed_commands.append({
            "container_id": container_id,
            "command": command,
            "kwargs": kwargs
        })
        return "Mock execution output"
