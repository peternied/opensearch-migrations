"""
Domain entity for snapshots.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from console_link.domain.exceptions.snapshot_errors import SnapshotValidationError


class SnapshotState(Enum):
    """Possible states for a snapshot."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class SnapshotType(Enum):
    """Types of snapshot repositories."""
    S3 = "s3"
    FILESYSTEM = "filesystem"


@dataclass
class SnapshotEntity:
    """Domain entity representing a snapshot.
    
    This entity encapsulates the core business data for a snapshot,
    independent of any infrastructure or presentation concerns.
    """
    # Core identifiers
    name: str
    repository_name: str
    type: SnapshotType
    
    # State information
    state: SnapshotState = SnapshotState.PENDING
    
    # Progress metrics
    percentage_completed: float = 0.0
    eta_ms: Optional[float] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Data metrics
    data_total_bytes: Optional[int] = None
    data_processed_bytes: Optional[int] = None
    data_throughput_bytes_avg_sec: Optional[float] = None
    
    # Shard metrics
    shard_total: Optional[int] = None
    shard_complete: Optional[int] = None
    shard_failed: Optional[int] = None
    
    # Configuration details (based on type)
    s3_uri: Optional[str] = None
    s3_region: Optional[str] = None
    s3_role_arn: Optional[str] = None
    s3_endpoint: Optional[str] = None
    filesystem_path: Optional[str] = None
    
    # Additional settings
    otel_endpoint: Optional[str] = None
    max_snapshot_rate_mb_per_node: Optional[int] = None
    
    def __post_init__(self):
        """Validate entity invariants after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate the snapshot entity data."""
        if not self.name:
            raise SnapshotValidationError("Snapshot name cannot be empty")
        
        if not self.repository_name:
            raise SnapshotValidationError("Repository name cannot be empty")
        
        if not isinstance(self.state, SnapshotState):
            raise SnapshotValidationError(f"Invalid snapshot state: {self.state}")
        
        if not isinstance(self.type, SnapshotType):
            raise SnapshotValidationError(f"Invalid snapshot type: {self.type}")
        
        if self.percentage_completed < 0 or self.percentage_completed > 100:
            raise SnapshotValidationError(
                f"Percentage completed must be between 0 and 100, got {self.percentage_completed}"
            )
        
        # Type-specific validation
        if self.type == SnapshotType.S3:
            if not self.s3_uri:
                raise SnapshotValidationError("S3 URI is required for S3 snapshots")
            if not self.s3_region:
                raise SnapshotValidationError("S3 region is required for S3 snapshots")
        elif self.type == SnapshotType.FILESYSTEM:
            if not self.filesystem_path:
                raise SnapshotValidationError("Filesystem path is required for filesystem snapshots")
    
    def is_complete(self) -> bool:
        """Check if the snapshot is complete."""
        return self.state == SnapshotState.SUCCESS
    
    def is_failed(self) -> bool:
        """Check if the snapshot has failed."""
        return self.state in (SnapshotState.FAILED, SnapshotState.PARTIAL)
    
    def is_in_progress(self) -> bool:
        """Check if the snapshot is currently in progress."""
        return self.state == SnapshotState.IN_PROGRESS
    
    def update_progress(
        self,
        percentage: float,
        processed_bytes: Optional[int] = None,
        eta_ms: Optional[float] = None
    ):
        """Update snapshot progress metrics."""
        self.percentage_completed = percentage
        if processed_bytes is not None:
            self.data_processed_bytes = processed_bytes
        if eta_ms is not None:
            self.eta_ms = eta_ms
        self.updated_at = datetime.utcnow()
    
    def mark_as_started(self):
        """Mark the snapshot as started."""
        self.state = SnapshotState.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self):
        """Mark the snapshot as successfully completed."""
        self.state = SnapshotState.SUCCESS
        self.percentage_completed = 100.0
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.eta_ms = 0.0
    
    def mark_as_failed(self, partial: bool = False):
        """Mark the snapshot as failed."""
        self.state = SnapshotState.PARTIAL if partial else SnapshotState.FAILED
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate the duration of the snapshot in milliseconds."""
        if not self.started_at:
            return None
        
        end_time = self.finished_at or datetime.utcnow()
        duration = end_time - self.started_at
        return duration.total_seconds() * 1000
    
    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotEntity":
        """Create a SnapshotEntity from a dictionary.
        
        This is useful for deserializing from API responses or databases.
        """
        # Convert string state to enum if needed
        if "state" in data and isinstance(data["state"], str):
            data["state"] = SnapshotState[data["state"]]
        
        # Convert string type to enum if needed
        if "type" in data and isinstance(data["type"], str):
            data["type"] = SnapshotType[data["type"]]
        
        # Convert string timestamps to datetime objects
        for field_name in ["started_at", "finished_at", "created_at", "updated_at"]:
            if field_name in data and data[field_name] and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name].replace("Z", "+00:00"))
        
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert the entity to a dictionary.
        
        This is useful for serializing to APIs or databases.
        """
        result = {
            "name": self.name,
            "repository_name": self.repository_name,
            "type": self.type.value,
            "state": self.state.value,
            "percentage_completed": self.percentage_completed,
            "eta_ms": self.eta_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "data_total_bytes": self.data_total_bytes,
            "data_processed_bytes": self.data_processed_bytes,
            "data_throughput_bytes_avg_sec": self.data_throughput_bytes_avg_sec,
            "shard_total": self.shard_total,
            "shard_complete": self.shard_complete,
            "shard_failed": self.shard_failed,
            "s3_uri": self.s3_uri,
            "s3_region": self.s3_region,
            "s3_role_arn": self.s3_role_arn,
            "s3_endpoint": self.s3_endpoint,
            "filesystem_path": self.filesystem_path,
            "otel_endpoint": self.otel_endpoint,
            "max_snapshot_rate_mb_per_node": self.max_snapshot_rate_mb_per_node,
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
