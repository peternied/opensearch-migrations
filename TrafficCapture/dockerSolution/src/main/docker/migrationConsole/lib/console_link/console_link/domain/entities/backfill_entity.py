"""
Domain entity for backfill operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

from console_link.domain.exceptions.backfill_errors import BackfillValidationError


class BackfillType(Enum):
    """Types of backfill operations."""
    OPENSEARCH_INGESTION = "opensearch_ingestion"
    REINDEX_FROM_SNAPSHOT = "reindex_from_snapshot"


class BackfillStatus(Enum):
    """Status of a backfill operation."""
    NOT_STARTED = "NOT_STARTED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    TERMINATING = "TERMINATING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class BackfillState(Enum):
    """Detailed state of backfill progress."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class BackfillEntity:
    """Domain entity representing a backfill operation.
    
    This entity encapsulates the core business data for a backfill,
    independent of any infrastructure or presentation concerns.
    """
    # Core identifiers
    id: str
    type: BackfillType
    
    # Status information
    status: BackfillStatus = BackfillStatus.NOT_STARTED
    state: BackfillState = BackfillState.PENDING
    
    # Progress metrics
    percentage_completed: float = 0.0
    eta_ms: Optional[float] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Shard metrics
    shard_total: Optional[int] = None
    shard_complete: Optional[int] = None
    shard_failed: Optional[int] = None
    shard_in_progress: Optional[int] = None
    shard_waiting: Optional[int] = None
    
    # Configuration
    config: Dict = field(default_factory=dict)
    
    # Scaling
    scale_units: int = 1
    
    # Error information
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate entity invariants after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate the backfill entity data."""
        if not self.id:
            raise BackfillValidationError("Backfill ID cannot be empty")
        
        if not isinstance(self.type, BackfillType):
            raise BackfillValidationError(f"Invalid backfill type: {self.type}")
        
        if not isinstance(self.status, BackfillStatus):
            raise BackfillValidationError(f"Invalid backfill status: {self.status}")
        
        if not isinstance(self.state, BackfillState):
            raise BackfillValidationError(f"Invalid backfill state: {self.state}")
        
        if self.percentage_completed < 0 or self.percentage_completed > 100:
            raise BackfillValidationError(
                f"Percentage completed must be between 0 and 100, got {self.percentage_completed}"
            )
        
        if self.scale_units < 0:
            raise BackfillValidationError(f"Scale units must be non-negative, got {self.scale_units}")
    
    @property
    def is_running(self) -> bool:
        """Check if the backfill is currently running."""
        return self.status == BackfillStatus.RUNNING
    
    @property
    def is_complete(self) -> bool:
        """Check if the backfill is complete."""
        return self.status == BackfillStatus.COMPLETED or self.state == BackfillState.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if the backfill has failed."""
        return self.status == BackfillStatus.FAILED or self.state == BackfillState.FAILED
    
    @property
    def can_start(self) -> bool:
        """Check if the backfill can be started."""
        return self.status in (BackfillStatus.NOT_STARTED, BackfillStatus.STOPPED)
    
    @property
    def can_stop(self) -> bool:
        """Check if the backfill can be stopped."""
        return self.status in (BackfillStatus.STARTING, BackfillStatus.RUNNING)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate the duration of the backfill in milliseconds."""
        if not self.started_at:
            return None
        
        end_time = self.finished_at or datetime.utcnow()
        duration = end_time - self.started_at
        return duration.total_seconds() * 1000
    
    def start(self):
        """Mark the backfill as started."""
        self.status = BackfillStatus.RUNNING
        self.state = BackfillState.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def stop(self):
        """Mark the backfill as stopped."""
        self.status = BackfillStatus.STOPPED
        self.state = BackfillState.CANCELLED
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def pause(self):
        """Mark the backfill as paused."""
        self.state = BackfillState.PAUSED
        self.updated_at = datetime.utcnow()
    
    def complete(self):
        """Mark the backfill as completed."""
        self.status = BackfillStatus.COMPLETED
        self.state = BackfillState.COMPLETED
        self.percentage_completed = 100.0
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.eta_ms = 0.0
    
    def fail(self, error_message: str):
        """Mark the backfill as failed."""
        self.status = BackfillStatus.FAILED
        self.state = BackfillState.FAILED
        self.error_message = error_message
        self.finished_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_progress(
        self,
        percentage: float,
        shard_complete: Optional[int] = None,
        shard_in_progress: Optional[int] = None,
        shard_waiting: Optional[int] = None,
        eta_ms: Optional[float] = None
    ):
        """Update backfill progress metrics."""
        self.percentage_completed = percentage
        if shard_complete is not None:
            self.shard_complete = shard_complete
        if shard_in_progress is not None:
            self.shard_in_progress = shard_in_progress
        if shard_waiting is not None:
            self.shard_waiting = shard_waiting
        if eta_ms is not None:
            self.eta_ms = eta_ms
        self.updated_at = datetime.utcnow()
    
    def scale(self, units: int):
        """Update the scale units for the backfill."""
        if units < 0:
            raise BackfillValidationError("Scale units must be non-negative")
        self.scale_units = units
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: dict) -> "BackfillEntity":
        """Create a BackfillEntity from a dictionary.
        
        This is useful for deserializing from API responses or databases.
        """
        # Convert string enums if needed
        if "type" in data and isinstance(data["type"], str):
            data["type"] = BackfillType(data["type"])
        
        if "status" in data and isinstance(data["status"], str):
            data["status"] = BackfillStatus(data["status"])
        
        if "state" in data and isinstance(data["state"], str):
            data["state"] = BackfillState(data["state"])
        
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
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "state": self.state.value,
            "percentage_completed": self.percentage_completed,
            "eta_ms": self.eta_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "shard_total": self.shard_total,
            "shard_complete": self.shard_complete,
            "shard_failed": self.shard_failed,
            "shard_in_progress": self.shard_in_progress,
            "shard_waiting": self.shard_waiting,
            "config": self.config,
            "scale_units": self.scale_units,
            "error_message": self.error_message,
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
