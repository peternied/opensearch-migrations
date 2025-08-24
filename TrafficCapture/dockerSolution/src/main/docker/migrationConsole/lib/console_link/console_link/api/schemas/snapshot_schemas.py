"""Pydantic schemas for snapshot API endpoints."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

from console_link.domain.entities.snapshot_entity import SnapshotState


class SnapshotType(str, Enum):
    """Snapshot type enumeration."""
    S3 = "s3"
    FILESYSTEM = "filesystem"


class CreateSnapshotRequest(BaseModel):
    """Request schema for creating a snapshot."""
    snapshot_name: str = Field(..., description="Name of the snapshot")
    repository_name: str = Field(..., description="Name of the snapshot repository")
    
    class Config:
        extra = 'forbid'


class SnapshotResponse(BaseModel):
    """Response schema for snapshot operations."""
    id: str = Field(..., description="Unique identifier for the snapshot")
    name: str = Field(..., description="Name of the snapshot")
    repository_name: str = Field(..., description="Name of the snapshot repository")
    state: SnapshotState = Field(..., description="Current state of the snapshot")
    start_time: Optional[datetime] = Field(None, description="When the snapshot started")
    end_time: Optional[datetime] = Field(None, description="When the snapshot completed")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    indices: List[str] = Field(default_factory=list, description="List of indices in the snapshot")
    shards_stats: Optional[Dict[str, int]] = Field(None, description="Shard statistics")
    failures: List[Dict[str, Any]] = Field(default_factory=list, description="Any failures encountered")
    
    class Config:
        orm_mode = True
        from_attributes = True
    
    @classmethod
    def from_entity(cls, entity) -> "SnapshotResponse":
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            repository_name=entity.repository_name,
            state=entity.state,
            start_time=entity.start_time,
            end_time=entity.end_time,
            duration_ms=entity.duration_ms,
            indices=entity.indices or [],
            shards_stats=entity.shards_stats,
            failures=entity.failures or []
        )


class SnapshotStatusResponse(BaseModel):
    """Response schema for snapshot status."""
    state: SnapshotState = Field(..., description="Current state of the snapshot")
    percentage_completed: float = Field(..., ge=0, le=100, description="Completion percentage")
    eta_ms: Optional[int] = Field(None, description="Estimated time to completion in milliseconds")
    shards_stats: Optional[Dict[str, int]] = Field(None, description="Shard statistics")
    indices_progress: Optional[Dict[str, float]] = Field(None, description="Per-index progress")
    
    class Config:
        orm_mode = True
        from_attributes = True


class SnapshotListResponse(BaseModel):
    """Response schema for listing snapshots."""
    snapshots: List[SnapshotResponse] = Field(..., description="List of snapshots")
    total: int = Field(..., description="Total number of snapshots")
    
    class Config:
        orm_mode = True
        from_attributes = True


class SnapshotRepositoryRequest(BaseModel):
    """Request schema for creating a snapshot repository."""
    name: str = Field(..., description="Repository name")
    type: SnapshotType = Field(..., description="Repository type")
    settings: Dict[str, Any] = Field(..., description="Repository-specific settings")
    
    class Config:
        extra = 'forbid'


class SnapshotRepositoryResponse(BaseModel):
    """Response schema for snapshot repository operations."""
    name: str = Field(..., description="Repository name")
    type: SnapshotType = Field(..., description="Repository type")
    settings: Dict[str, Any] = Field(..., description="Repository settings")
    verified: bool = Field(False, description="Whether the repository is verified")
    
    class Config:
        orm_mode = True
        from_attributes = True
