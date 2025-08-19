from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WorkItemStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"


class ProgressUpdate(BaseModel):
    documents_processed: int = Field(ge=0, description="Number of documents processed")
    bytes_processed: int = Field(ge=0, description="Number of bytes processed")


class BackfillWorkItem(BaseModel):
    work_item_id: str = Field(..., description="Unique identifier for the work item")
    session_name: str = Field(..., description="Name of the migration session")
    status: WorkItemStatus = Field(default=WorkItemStatus.PENDING, description="Current status of the work item")
    
    # Shard metadata
    index_name: str = Field(..., description="Name of the Elasticsearch/OpenSearch index")
    shard_number: int = Field(ge=0, description="Shard number within the index")
    document_count: int = Field(ge=0, description="Total number of documents in this shard")
    total_size_bytes: int = Field(ge=0, description="Total size of documents in bytes")
    
    # Lease management
    worker_id: Optional[str] = Field(None, description="ID of the worker that has the lease")
    lease_expiry: Optional[datetime] = Field(None, description="When the current lease expires")
    
    # Progress tracking
    documents_processed: int = Field(default=0, ge=0, description="Number of documents processed so far")
    bytes_processed: int = Field(default=0, ge=0, description="Number of bytes processed so far")
    last_progress_update: Optional[datetime] = Field(None, description="Timestamp of last progress update")
    
    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the work item was created")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")

    def progress_percentage(self) -> float:
        """Calculate progress percentage based on documents processed."""
        if self.document_count == 0:
            return 100.0 if self.status == WorkItemStatus.COMPLETED else 0.0
        return min(100.0, (self.documents_processed / self.document_count) * 100.0)

    def is_lease_expired(self) -> bool:
        """Check if the current lease has expired."""
        if self.lease_expiry is None:
            return False
        return datetime.now(timezone.utc) > self.lease_expiry


class CreateWorkItemRequest(BaseModel):
    work_item_id: str = Field(..., description="Unique identifier for the work item")
    index_name: str = Field(..., description="Name of the Elasticsearch/OpenSearch index")
    shard_number: int = Field(ge=0, description="Shard number within the index")
    document_count: int = Field(ge=0, description="Total number of documents in this shard")
    total_size_bytes: int = Field(ge=0, description="Total size of documents in bytes")


class LeaseRenewalRequest(BaseModel):
    worker_id: str = Field(..., description="ID of the worker requesting lease renewal")
    progress: Optional[ProgressUpdate] = Field(None, description="Optional progress update")


class AcquireWorkItemResponse(BaseModel):
    work_item: BackfillWorkItem
    lease_duration_seconds: int = Field(default=300, description="Duration of the lease in seconds")


class WorkQueueStatus(BaseModel):
    session_name: str = Field(..., description="Name of the migration session")
    total_work_items: int = Field(ge=0, description="Total number of work items")
    pending_work_items: int = Field(ge=0, description="Number of pending work items")
    assigned_work_items: int = Field(ge=0, description="Number of assigned work items")
    completed_work_items: int = Field(ge=0, description="Number of completed work items")
    
    # Progress aggregates
    total_documents: int = Field(ge=0, description="Total documents across all work items")
    total_documents_processed: int = Field(ge=0, description="Total documents processed")
    total_size_bytes: int = Field(ge=0, description="Total size in bytes across all work items")
    total_bytes_processed: int = Field(ge=0, description="Total bytes processed")
    
    # Timing
    started_at: Optional[datetime] = Field(None, description="When the first work item was started")
    last_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last status update time")

    def overall_progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_documents == 0:
            return 100.0 if self.completed_work_items == self.total_work_items else 0.0
        return min(100.0, (self.total_documents_processed / self.total_documents) * 100.0)
