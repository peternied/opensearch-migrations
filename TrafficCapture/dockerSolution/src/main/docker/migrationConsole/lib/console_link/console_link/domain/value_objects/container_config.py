"""Value objects for container configuration.

This module defines immutable value objects for container-related configurations
used in the console_link application.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from console_link.domain.exceptions.common_errors import ValidationError


class ContainerRuntime(Enum):
    """Supported container runtime environments."""
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    ECS = "ecs"


@dataclass(frozen=True)
class ContainerConfig:
    """Base configuration for container operations.
    
    This immutable value object encapsulates container configuration details.
    """
    image: str
    runtime: ContainerRuntime
    environment: Dict[str, str] = field(default_factory=dict)
    cpu: Optional[int] = None
    memory: Optional[int] = None
    
    def __post_init__(self):
        """Validate container configuration."""
        if not self.image:
            raise ValidationError("Container image cannot be empty")
        
        if not isinstance(self.runtime, ContainerRuntime):
            raise ValidationError(f"Invalid container runtime: {self.runtime}")
        
        if self.cpu is not None and self.cpu <= 0:
            raise ValidationError(f"CPU must be positive, got {self.cpu}")
        
        if self.memory is not None and self.memory <= 0:
            raise ValidationError(f"Memory must be positive, got {self.memory}")
    
    @classmethod
    def from_dict(cls, data: dict) -> "ContainerConfig":
        """Create a ContainerConfig from a dictionary."""
        runtime_str = data.get("runtime", "docker")
        try:
            runtime = ContainerRuntime(runtime_str)
        except ValueError:
            runtime = ContainerRuntime.DOCKER
        
        return cls(
            image=data.get("image", ""),
            runtime=runtime,
            environment=data.get("environment", {}),
            cpu=data.get("cpu"),
            memory=data.get("memory")
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "image": self.image,
            "runtime": self.runtime.value,
            "environment": self.environment,
        }
        if self.cpu is not None:
            result["cpu"] = self.cpu
        if self.memory is not None:
            result["memory"] = self.memory
        return result


@dataclass(frozen=True)
class DockerConfig(ContainerConfig):
    """Configuration specific to Docker containers."""
    network: Optional[str] = None
    volumes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure runtime is Docker and validate configuration."""
        super().__post_init__()
        if self.runtime != ContainerRuntime.DOCKER:
            object.__setattr__(self, 'runtime', ContainerRuntime.DOCKER)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        if self.network:
            result["network"] = self.network
        if self.volumes:
            result["volumes"] = self.volumes
        return result


@dataclass(frozen=True)
class KubernetesConfig(ContainerConfig):
    """Configuration specific to Kubernetes deployments."""
    namespace: str = "default"
    replicas: int = 1
    service_name: Optional[str] = None
    
    def __post_init__(self):
        """Ensure runtime is Kubernetes and validate configuration."""
        super().__post_init__()
        if self.runtime != ContainerRuntime.KUBERNETES:
            object.__setattr__(self, 'runtime', ContainerRuntime.KUBERNETES)
        
        if self.replicas < 1:
            raise ValidationError(f"Replicas must be at least 1, got {self.replicas}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result["namespace"] = self.namespace
        result["replicas"] = self.replicas
        if self.service_name:
            result["service_name"] = self.service_name
        return result


@dataclass(frozen=True)
class ECSConfig(ContainerConfig):
    """Configuration specific to AWS ECS."""
    cluster_name: str = ""
    task_definition: str = ""
    service_name: Optional[str] = None
    desired_count: int = 1
    
    def __post_init__(self):
        """Ensure runtime is ECS and validate configuration."""
        super().__post_init__()
        if self.runtime != ContainerRuntime.ECS:
            object.__setattr__(self, 'runtime', ContainerRuntime.ECS)
        
        if not self.cluster_name:
            raise ValidationError("ECS cluster_name cannot be empty")
        
        if not self.task_definition:
            raise ValidationError("ECS task_definition cannot be empty")
        
        if self.desired_count < 1:
            raise ValidationError(f"Desired count must be at least 1, got {self.desired_count}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result["cluster_name"] = self.cluster_name
        result["task_definition"] = self.task_definition
        result["desired_count"] = self.desired_count
        if self.service_name:
            result["service_name"] = self.service_name
        return result
