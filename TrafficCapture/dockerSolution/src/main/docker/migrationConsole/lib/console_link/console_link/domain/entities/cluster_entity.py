"""
Domain entity for clusters.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from console_link.domain.exceptions.cluster_errors import ClusterValidationError
from console_link.domain.value_objects.auth_config import AuthConfig


class ClusterType(Enum):
    """Types of clusters."""
    ELASTICSEARCH = "elasticsearch"
    OPENSEARCH = "opensearch"


class ClusterRole(Enum):
    """Roles that a cluster can have in a migration."""
    SOURCE = "source"
    TARGET = "target"
    MONITORING = "monitoring"


class ClusterStatus(Enum):
    """Status of a cluster connection."""
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNREACHABLE = "unreachable"
    UNHEALTHY = "unhealthy"
    HEALTHY = "healthy"


@dataclass
class ClusterEntity:
    """Domain entity representing an Elasticsearch or OpenSearch cluster.
    
    This entity encapsulates the core business data for a cluster,
    independent of any infrastructure or presentation concerns.
    """
    # Core identifiers
    endpoint: str
    role: ClusterRole
    
    # Cluster details
    type: ClusterType = ClusterType.OPENSEARCH
    version: Optional[str] = None
    name: Optional[str] = None
    
    # Security settings
    allow_insecure: bool = False
    auth_config: Optional[AuthConfig] = None
    
    # Status information
    status: ClusterStatus = ClusterStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    health_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Cluster metadata
    node_count: Optional[int] = None
    index_count: Optional[int] = None
    document_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    
    def __post_init__(self):
        """Validate entity invariants after initialization."""
        self._validate()
        
        # If endpoint starts with https and allow_insecure is not set, default to False
        # If endpoint starts with http and allow_insecure is not set, default to True
        if self.endpoint.startswith("https://") and self.allow_insecure is None:
            self.allow_insecure = False
        elif self.endpoint.startswith("http://") and self.allow_insecure is None:
            self.allow_insecure = True
    
    def _validate(self):
        """Validate the cluster entity data."""
        if not self.endpoint:
            raise ClusterValidationError("Cluster endpoint cannot be empty")
        
        if not self.endpoint.startswith(("http://", "https://")):
            raise ClusterValidationError(
                f"Cluster endpoint must start with http:// or https://, got: {self.endpoint}"
            )
        
        if not isinstance(self.role, ClusterRole):
            raise ClusterValidationError(f"Invalid cluster role: {self.role}")
        
        if not isinstance(self.type, ClusterType):
            raise ClusterValidationError(f"Invalid cluster type: {self.type}")
        
        if not isinstance(self.status, ClusterStatus):
            raise ClusterValidationError(f"Invalid cluster status: {self.status}")
        
        # Validate version format if provided
        if self.version and not self._is_valid_version(self.version):
            raise ClusterValidationError(f"Invalid version format: {self.version}")
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is in valid format (e.g., '7.10.2', '2.11.0')."""
        parts = version.split('.')
        if len(parts) < 2 or len(parts) > 3:
            return False
        return all(part.isdigit() for part in parts)
    
    @property
    def is_source(self) -> bool:
        """Check if this is a source cluster."""
        return self.role == ClusterRole.SOURCE
    
    @property
    def is_target(self) -> bool:
        """Check if this is a target cluster."""
        return self.role == ClusterRole.TARGET
    
    @property
    def is_healthy(self) -> bool:
        """Check if the cluster is healthy."""
        return self.status == ClusterStatus.HEALTHY
    
    @property
    def is_connected(self) -> bool:
        """Check if the cluster is connected."""
        return self.status in (ClusterStatus.CONNECTED, ClusterStatus.HEALTHY)
    
    @property
    def is_secure(self) -> bool:
        """Check if the cluster uses HTTPS."""
        return self.endpoint.startswith("https://")
    
    @property
    def display_name(self) -> str:
        """Get a display name for the cluster."""
        if self.name:
            return self.name
        # Extract hostname from endpoint
        endpoint = self.endpoint.rstrip('/')
        if '://' in endpoint:
            endpoint = endpoint.split('://', 1)[1]
        if '/' in endpoint:
            endpoint = endpoint.split('/', 1)[0]
        return endpoint
    
    def update_status(self, status: ClusterStatus, message: Optional[str] = None):
        """Update the cluster's status."""
        self.status = status
        self.last_health_check = datetime.utcnow()
        self.health_message = message
        self.updated_at = datetime.utcnow()
    
    def update_metadata(
        self,
        node_count: Optional[int] = None,
        index_count: Optional[int] = None,
        document_count: Optional[int] = None,
        total_size_bytes: Optional[int] = None
    ):
        """Update cluster metadata."""
        if node_count is not None:
            self.node_count = node_count
        if index_count is not None:
            self.index_count = index_count
        if document_count is not None:
            self.document_count = document_count
        if total_size_bytes is not None:
            self.total_size_bytes = total_size_bytes
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: dict) -> "ClusterEntity":
        """Create a ClusterEntity from a dictionary.
        
        This is useful for deserializing from API responses or databases.
        """
        # Convert string enums if needed
        if "role" in data and isinstance(data["role"], str):
            data["role"] = ClusterRole(data["role"])
        
        if "type" in data and isinstance(data["type"], str):
            data["type"] = ClusterType(data["type"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ClusterStatus(data["status"])
        
        # Convert auth_config dict to AuthConfig object if present
        if "auth_config" in data and isinstance(data["auth_config"], dict):
            data["auth_config"] = AuthConfig.from_dict(data["auth_config"])
        
        # Convert string timestamps to datetime objects
        for field_name in ["last_health_check", "created_at", "updated_at"]:
            if field_name in data and data[field_name] and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert the entity to a dictionary.
        
        This is useful for serializing to APIs or databases.
        """
        result = {
            "endpoint": self.endpoint,
            "role": self.role.value,
            "type": self.type.value,
            "version": self.version,
            "name": self.name,
            "allow_insecure": self.allow_insecure,
            "auth_config": self.auth_config.to_dict() if self.auth_config else None,
            "status": self.status.value,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_message": self.health_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "node_count": self.node_count,
            "index_count": self.index_count,
            "document_count": self.document_count,
            "total_size_bytes": self.total_size_bytes,
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
