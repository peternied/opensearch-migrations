from datetime import datetime, timezone, timedelta
from typing import List, Optional
from tinydb import TinyDB, Query

from console_link.models.backfill_work_item import (
    BackfillWorkItem,
    WorkItemStatus,
    WorkQueueStatus,
    ProgressUpdate
)

# Use a separate database file for backfill work items
db = TinyDB("backfill_work_db.json")
_work_items_table = db.table("work_items")

# Default lease duration in seconds (5 minutes)
DEFAULT_LEASE_DURATION_SECONDS = 300


def create_work_item(work_item: BackfillWorkItem) -> BackfillWorkItem:
    """Create a new work item."""
    # Check if work item already exists
    if find_work_item(work_item.session_name, work_item.work_item_id):
        raise WorkItemAlreadyExists(f"Work item {work_item.work_item_id} already exists in session {work_item.session_name}")
    
    work_item_data = work_item.model_dump()
    _work_items_table.insert(work_item_data)
    return work_item


def find_work_item(session_name: str, work_item_id: str) -> Optional[BackfillWorkItem]:
    """Find a work item by session and ID."""
    work_item_query = Query()
    result = _work_items_table.get(
        (work_item_query.session_name == session_name) & 
        (work_item_query.work_item_id == work_item_id)
    )
    
    if result:
        return BackfillWorkItem.model_validate(result)
    return None


def update_work_item(work_item: BackfillWorkItem) -> BackfillWorkItem:
    """Update an existing work item."""
    work_item_query = Query()
    work_item_data = work_item.model_dump()
    
    updated_count = _work_items_table.update(
        work_item_data,
        (work_item_query.session_name == work_item.session_name) & 
        (work_item_query.work_item_id == work_item.work_item_id)
    )
    
    if updated_count == 0:
        raise WorkItemNotFound(f"Work item {work_item.work_item_id} not found in session {work_item.session_name}")
    
    return work_item


def acquire_next_work_item(session_name: str, worker_id: str, lease_duration_seconds: int = DEFAULT_LEASE_DURATION_SECONDS) -> Optional[BackfillWorkItem]:
    """Acquire the next available work item for a worker."""
    work_item_query = Query()
    current_time = datetime.now(timezone.utc)
    lease_expiry = current_time + timedelta(seconds=lease_duration_seconds)
    
    # Find available work items (pending or expired leases)
    available_items = _work_items_table.search(
        (work_item_query.session_name == session_name) & 
        ((work_item_query.status == WorkItemStatus.PENDING) |
         ((work_item_query.status == WorkItemStatus.ASSIGNED) & 
          (work_item_query.lease_expiry < current_time.isoformat())))
    )
    
    if not available_items:
        return None
    
    # Take the first available item (could add prioritization logic here)
    item_data = available_items[0]
    work_item = BackfillWorkItem.model_validate(item_data)
    
    # Update the work item with lease information
    work_item.status = WorkItemStatus.ASSIGNED
    work_item.worker_id = worker_id
    work_item.lease_expiry = lease_expiry
    
    if work_item.started_at is None:
        work_item.started_at = current_time
    
    return update_work_item(work_item)


def renew_lease(session_name: str, work_item_id: str, worker_id: str, 
                lease_duration_seconds: int = DEFAULT_LEASE_DURATION_SECONDS,
                progress: Optional[ProgressUpdate] = None) -> BackfillWorkItem:
    """Renew a lease for a work item and optionally update progress."""
    work_item = find_work_item(session_name, work_item_id)
    if not work_item:
        raise WorkItemNotFound(f"Work item {work_item_id} not found in session {session_name}")
    
    # Verify the worker owns the lease
    if work_item.worker_id != worker_id:
        raise LeaseNotOwnedByWorker(f"Work item {work_item_id} is not owned by worker {worker_id}")
    
    # Check if lease has expired
    if work_item.is_lease_expired():
        raise LeaseExpired(f"Lease for work item {work_item_id} has expired")
    
    current_time = datetime.now(timezone.utc)
    work_item.lease_expiry = current_time + timedelta(seconds=lease_duration_seconds)
    
    # Update progress if provided
    if progress:
        work_item.documents_processed = progress.documents_processed
        work_item.bytes_processed = progress.bytes_processed
        work_item.last_progress_update = current_time
    
    return update_work_item(work_item)


def complete_work_item(session_name: str, work_item_id: str, worker_id: str) -> BackfillWorkItem:
    """Mark a work item as completed."""
    work_item = find_work_item(session_name, work_item_id)
    if not work_item:
        raise WorkItemNotFound(f"Work item {work_item_id} not found in session {session_name}")
    
    # Verify the worker owns the lease
    if work_item.worker_id != worker_id:
        raise LeaseNotOwnedByWorker(f"Work item {work_item_id} is not owned by worker {worker_id}")
    
    # Check if lease has expired
    if work_item.is_lease_expired():
        raise LeaseExpired(f"Lease for work item {work_item_id} has expired")
    
    current_time = datetime.now(timezone.utc)
    work_item.status = WorkItemStatus.COMPLETED
    work_item.completed_at = current_time
    work_item.lease_expiry = None  # Clear the lease
    
    return update_work_item(work_item)


def get_work_queue_status(session_name: str) -> WorkQueueStatus:
    """Get the status of the work queue for a session."""
    work_item_query = Query()
    all_items = _work_items_table.search(work_item_query.session_name == session_name)
    
    if not all_items:
        return WorkQueueStatus(
            session_name=session_name,
            total_work_items=0,
            pending_work_items=0,
            assigned_work_items=0,
            completed_work_items=0,
            total_documents=0,
            total_documents_processed=0,
            total_size_bytes=0,
            total_bytes_processed=0,
            started_at=None
        )
    
    work_items = [BackfillWorkItem.model_validate(item) for item in all_items]
    current_time = datetime.now(timezone.utc)
    
    # Count items by status (accounting for expired leases)
    pending_count = 0
    assigned_count = 0
    completed_count = 0
    
    total_documents = 0
    total_documents_processed = 0
    total_size_bytes = 0
    total_bytes_processed = 0
    
    earliest_start_time = None
    
    for item in work_items:
        # Aggregate metrics
        total_documents += item.document_count
        total_documents_processed += item.documents_processed
        total_size_bytes += item.total_size_bytes
        total_bytes_processed += item.bytes_processed
        
        # Track earliest start time
        if item.started_at and (earliest_start_time is None or item.started_at < earliest_start_time):
            earliest_start_time = item.started_at
        
        # Count by effective status
        if item.status == WorkItemStatus.COMPLETED:
            completed_count += 1
        elif item.status == WorkItemStatus.ASSIGNED and not item.is_lease_expired():
            assigned_count += 1
        else:
            pending_count += 1
    
    return WorkQueueStatus(
        session_name=session_name,
        total_work_items=len(work_items),
        pending_work_items=pending_count,
        assigned_work_items=assigned_count,
        completed_work_items=completed_count,
        total_documents=total_documents,
        total_documents_processed=total_documents_processed,
        total_size_bytes=total_size_bytes,
        total_bytes_processed=total_bytes_processed,
        started_at=earliest_start_time
    )


def list_work_items_by_session(session_name: str) -> List[BackfillWorkItem]:
    """List all work items for a session."""
    work_item_query = Query()
    items = _work_items_table.search(work_item_query.session_name == session_name)
    return [BackfillWorkItem.model_validate(item) for item in items]


def cleanup_expired_leases(session_name: str) -> int:
    """Clean up expired leases, making work items available again. Returns count of cleaned items."""
    work_item_query = Query()
    current_time = datetime.now(timezone.utc)
    
    expired_items = _work_items_table.search(
        (work_item_query.session_name == session_name) & 
        (work_item_query.status == WorkItemStatus.ASSIGNED) &
        (work_item_query.lease_expiry < current_time.isoformat())
    )
    
    cleanup_count = 0
    for item_data in expired_items:
        work_item = BackfillWorkItem.model_validate(item_data)
        work_item.status = WorkItemStatus.PENDING
        work_item.worker_id = None
        work_item.lease_expiry = None
        update_work_item(work_item)
        cleanup_count += 1
    
    return cleanup_count


def delete_work_items_by_session(session_name: str) -> int:
    """Delete all work items for a session. Returns count of deleted items."""
    work_item_query = Query()
    return len(_work_items_table.remove(work_item_query.session_name == session_name))


# Exception classes
class WorkItemNotFound(Exception):
    """Raised when a work item is not found."""
    pass


class WorkItemAlreadyExists(Exception):
    """Raised when trying to create a work item with an existing ID."""
    pass


class LeaseNotOwnedByWorker(Exception):
    """Raised when a worker tries to operate on a work item they don't own."""
    pass


class LeaseExpired(Exception):
    """Raised when trying to operate on an expired lease."""
    pass
