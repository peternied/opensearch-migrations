"""Common Pydantic schemas used across multiple endpoints."""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    
    class Config:
        extra = 'forbid'


class PaginatedResponse(BaseModel):
    """Base schema for paginated responses."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        orm_mode = True
        from_attributes = True


class TimestampedResponse(BaseModel):
    """Base schema for responses with timestamps."""
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True
        from_attributes = True


class OperationResult(BaseModel):
    """Generic operation result schema."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Result message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional result data")
    
    class Config:
        orm_mode = True
        from_attributes = True


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str = Field(..., description="Current status")
    message: Optional[str] = Field(None, description="Status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")
    
    class Config:
        orm_mode = True
        from_attributes = True


class VersionInfo(BaseModel):
    """Version information schema."""
    version: str = Field(..., description="Version string")
    build_date: Optional[datetime] = Field(None, description="Build date")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    
    class Config:
        orm_mode = True
        from_attributes = True


class SystemInfo(BaseModel):
    """System information schema."""
    hostname: str = Field(..., description="System hostname")
    platform: str = Field(..., description="Platform (e.g., linux, darwin)")
    python_version: str = Field(..., description="Python version")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    
    class Config:
        orm_mode = True
        from_attributes = True


class MetricValue(BaseModel):
    """Schema for a single metric value."""
    name: str = Field(..., description="Metric name")
    value: Union[int, float] = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    timestamp: datetime = Field(..., description="When the metric was collected")
    tags: Dict[str, str] = Field(default_factory=dict, description="Metric tags")
    
    class Config:
        orm_mode = True
        from_attributes = True


class MetricsResponse(BaseModel):
    """Response schema for metrics endpoints."""
    metrics: List[MetricValue] = Field(..., description="List of metrics")
    start_time: datetime = Field(..., description="Start of measurement period")
    end_time: datetime = Field(..., description="End of measurement period")
    
    class Config:
        orm_mode = True
        from_attributes = True


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncTaskResponse(BaseModel):
    """Response for asynchronous task operations."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="When the task was created")
    started_at: Optional[datetime] = Field(None, description="When the task started")
    completed_at: Optional[datetime] = Field(None, description="When the task completed")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BulkOperationRequest(BaseModel):
    """Request schema for bulk operations."""
    operations: List[Dict[str, Any]] = Field(..., description="List of operations to perform")
    continue_on_error: bool = Field(False, description="Whether to continue on error")
    
    class Config:
        extra = 'forbid'


class BulkOperationResult(BaseModel):
    """Result of a single operation in a bulk request."""
    index: int = Field(..., description="Operation index in the request")
    success: bool = Field(..., description="Whether the operation succeeded")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        orm_mode = True
        from_attributes = True


class BulkOperationResponse(BaseModel):
    """Response schema for bulk operations."""
    total: int = Field(..., description="Total number of operations")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: List[BulkOperationResult] = Field(..., description="Individual operation results")
    
    class Config:
        orm_mode = True
        from_attributes = True
