"""Pydantic schemas for backfill API endpoints."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class BackfillStatus(str, Enum):
    """Backfill status enumeration."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class BackfillType(str, Enum):
    """Backfill type enumeration."""
    RFS = "rfs"
    SNAPSHOT = "snapshot"


class CreateBackfillRequest(BaseModel):
    """Request schema for creating a backfill."""
    backfill_type: BackfillType = Field(..., description="Type of backfill")
    source_cluster_id: str = Field(..., description="Source cluster identifier")
    target_cluster_id: str = Field(..., description="Target cluster identifier")
    snapshot_name: Optional[str] = Field(None, description="Snapshot name for snapshot-based backfill")
    indices: Optional[List[str]] = Field(None, description="Specific indices to backfill")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    
    class Config:
        extra = 'forbid'


class BackfillResponse(BaseModel):
    """Response schema for backfill operations."""
    id: str = Field(..., description="Unique identifier for the backfill")
    backfill_type: BackfillType = Field(..., description="Type of backfill")
    status: BackfillStatus = Field(..., description="Current status of the backfill")
    source_cluster_id: str = Field(..., description="Source cluster identifier")
    target_cluster_id: str = Field(..., description="Target cluster identifier")
    start_time: Optional[datetime] = Field(None, description="When the backfill started")
    end_time: Optional[datetime] = Field(None, description="When the backfill completed")
    indices: List[str] = Field(default_factory=list, description="Indices being backfilled")
    documents_migrated: int = Field(0, description="Number of documents migrated")
    documents_total: Optional[int] = Field(None, description="Total number of documents to migrate")
    bytes_migrated: int = Field(0, description="Bytes migrated")
    bytes_total: Optional[int] = Field(None, description="Total bytes to migrate")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BackfillProgressResponse(BaseModel):
    """Response schema for backfill progress."""
    backfill_id: str = Field(..., description="Backfill identifier")
    status: BackfillStatus = Field(..., description="Current status")
    percentage_completed: float = Field(..., ge=0, le=100, description="Completion percentage")
    documents_migrated: int = Field(..., description="Documents migrated so far")
    documents_total: Optional[int] = Field(None, description="Total documents to migrate")
    bytes_migrated: int = Field(..., description="Bytes migrated so far")
    bytes_total: Optional[int] = Field(None, description="Total bytes to migrate")
    indices_completed: List[str] = Field(default_factory=list, description="Indices completed")
    indices_in_progress: List[str] = Field(default_factory=list, description="Indices in progress")
    indices_pending: List[str] = Field(default_factory=list, description="Indices pending")
    current_rate: Optional[float] = Field(None, description="Current migration rate (docs/sec)")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated time remaining in seconds")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BackfillListResponse(BaseModel):
    """Response schema for listing backfills."""
    backfills: List[BackfillResponse] = Field(..., description="List of backfills")
    total: int = Field(..., description="Total number of backfills")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BackfillCommandRequest(BaseModel):
    """Request schema for backfill commands (start, stop, pause, resume)."""
    command: str = Field(..., description="Command to execute", pattern="^(start|stop|pause|resume)$")
    reason: Optional[str] = Field(None, description="Reason for the command")
    
    class Config:
        extra = 'forbid'


class BackfillCommandResponse(BaseModel):
    """Response schema for backfill command execution."""
    success: bool = Field(..., description="Whether the command was successful")
    message: str = Field(..., description="Result message")
    new_status: BackfillStatus = Field(..., description="New backfill status")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BackfillWorkItem(BaseModel):
    """Schema for a backfill work item."""
    index_name: str = Field(..., description="Index name")
    shard_id: int = Field(..., description="Shard identifier")
    status: str = Field(..., description="Work item status")
    assigned_worker: Optional[str] = Field(None, description="Assigned worker ID")
    start_time: Optional[datetime] = Field(None, description="When work started")
    completion_time: Optional[datetime] = Field(None, description="When work completed")
    attempts: int = Field(0, description="Number of attempts")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BackfillWorkItemsResponse(BaseModel):
    """Response schema for backfill work items."""
    backfill_id: str = Field(..., description="Backfill identifier")
    work_items: List[BackfillWorkItem] = Field(..., description="List of work items")
    total: int = Field(..., description="Total number of work items")
    completed: int = Field(..., description="Number of completed items")
    in_progress: int = Field(..., description="Number of items in progress")
    failed: int = Field(..., description="Number of failed items")
    
    class Config:
        orm_mode = True
        from_attributes = True


class UpdateBackfillRequest(BaseModel):
    """Request schema for updating backfill configuration."""
    indices: Optional[List[str]] = Field(None, description="Update indices to backfill")
    config: Optional[Dict[str, Any]] = Field(None, description="Update configuration")
    
    class Config:
        extra = 'forbid'
