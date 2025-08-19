import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Body
from typing import List

from console_link.db import backfill_work_db
from console_link.models.backfill_work_item import (
    BackfillWorkItem,
    CreateWorkItemRequest,
    LeaseRenewalRequest,
    AcquireWorkItemResponse,
    WorkQueueStatus,
    ProgressUpdate
)
from console_link.api.sessions import http_safe_find_session

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

backfill_router = APIRouter(
    prefix="/backfill/work-items",
    tags=["backfill"],
)


@backfill_router.post("/",
                     response_model=BackfillWorkItem,
                     status_code=201,
                     operation_id="createBackfillWorkItem")
def create_work_item(session_name: str, request: CreateWorkItemRequest = Body(...)):
    """Create a new backfill work item."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        work_item = BackfillWorkItem(
            work_item_id=request.work_item_id,
            session_name=session_name,
            index_name=request.index_name,
            shard_number=request.shard_number,
            document_count=request.document_count,
            total_size_bytes=request.total_size_bytes
        )
        
        created_work_item = backfill_work_db.create_work_item(work_item)
        logger.info(f"Created work item {request.work_item_id} for session {session_name}")
        
        return created_work_item
        
    except backfill_work_db.WorkItemAlreadyExists:
        raise HTTPException(
            status_code=409, 
            detail=f"Work item {request.work_item_id} already exists in session {session_name}"
        )
    except Exception as e:
        logger.error(f"Failed to create work item {request.work_item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create work item: {str(e)}")


@backfill_router.post("/batch",
                      response_model=List[BackfillWorkItem],
                      status_code=201,
                      operation_id="createBackfillWorkItems")
def create_work_items_batch(session_name: str, requests: List[CreateWorkItemRequest] = Body(...)):
    """Create multiple backfill work items in batch."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    created_items = []
    failed_items = []
    
    for request in requests:
        try:
            work_item = BackfillWorkItem(
                work_item_id=request.work_item_id,
                session_name=session_name,
                index_name=request.index_name,
                shard_number=request.shard_number,
                document_count=request.document_count,
                total_size_bytes=request.total_size_bytes
            )
            
            created_work_item = backfill_work_db.create_work_item(work_item)
            created_items.append(created_work_item)
            
        except backfill_work_db.WorkItemAlreadyExists:
            failed_items.append(f"Work item {request.work_item_id} already exists")
        except Exception as e:
            failed_items.append(f"Failed to create work item {request.work_item_id}: {str(e)}")
    
    if failed_items:
        logger.warning(f"Some work items failed to create: {failed_items}")
    
    logger.info(f"Created {len(created_items)} work items for session {session_name}")
    return created_items


@backfill_router.get("/acquire",
                     response_model=AcquireWorkItemResponse,
                     operation_id="acquireBackfillWorkItem")
def acquire_work_item(session_name: str, worker_id: str):
    """Acquire the next available work item for a worker."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        # Clean up expired leases first
        cleanup_count = backfill_work_db.cleanup_expired_leases(session_name)
        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} expired leases for session {session_name}")
        
        work_item = backfill_work_db.acquire_next_work_item(session_name, worker_id)
        
        if not work_item:
            raise HTTPException(
                status_code=404,
                detail="No available work items"
            )
        
        logger.info(f"Worker {worker_id} acquired work item {work_item.work_item_id}")
        
        return AcquireWorkItemResponse(
            work_item=work_item,
            lease_duration_seconds=backfill_work_db.DEFAULT_LEASE_DURATION_SECONDS
        )
        
    except Exception as e:
        logger.error(f"Failed to acquire work item for worker {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acquire work item: {str(e)}")


@backfill_router.put("/{work_item_id}/lease",
                     response_model=BackfillWorkItem,
                     operation_id="renewBackfillWorkItemLease")
def renew_lease(session_name: str, work_item_id: str, request: LeaseRenewalRequest = Body(...)):
    """Renew a lease for a work item and optionally update progress."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        work_item = backfill_work_db.renew_lease(
            session_name=session_name,
            work_item_id=work_item_id,
            worker_id=request.worker_id,
            progress=request.progress
        )
        
        if request.progress:
            logger.info(f"Renewed lease for work item {work_item_id} with progress: "
                       f"{request.progress.documents_processed}/{work_item.document_count} docs, "
                       f"{request.progress.bytes_processed}/{work_item.total_size_bytes} bytes")
        else:
            logger.info(f"Renewed lease for work item {work_item_id}")
        
        return work_item
        
    except backfill_work_db.WorkItemNotFound:
        raise HTTPException(status_code=404, detail=f"Work item {work_item_id} not found")
    except backfill_work_db.LeaseNotOwnedByWorker:
        raise HTTPException(status_code=409, detail=f"Work item {work_item_id} is not owned by worker {request.worker_id}")
    except backfill_work_db.LeaseExpired:
        raise HTTPException(status_code=410, detail=f"Lease for work item {work_item_id} has expired")
    except Exception as e:
        logger.error(f"Failed to renew lease for work item {work_item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to renew lease: {str(e)}")


@backfill_router.put("/{work_item_id}/complete",
                     response_model=BackfillWorkItem,
                     operation_id="completeBackfillWorkItem")
def complete_work_item(session_name: str, work_item_id: str, worker_id: str = Body(...)):
    """Mark a work item as completed."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        work_item = backfill_work_db.complete_work_item(
            session_name=session_name,
            work_item_id=work_item_id,
            worker_id=worker_id
        )
        
        logger.info(f"Work item {work_item_id} completed by worker {worker_id}")
        return work_item
        
    except backfill_work_db.WorkItemNotFound:
        raise HTTPException(status_code=404, detail=f"Work item {work_item_id} not found")
    except backfill_work_db.LeaseNotOwnedByWorker:
        raise HTTPException(status_code=409, detail=f"Work item {work_item_id} is not owned by worker {worker_id}")
    except backfill_work_db.LeaseExpired:
        raise HTTPException(status_code=410, detail=f"Lease for work item {work_item_id} has expired")
    except Exception as e:
        logger.error(f"Failed to complete work item {work_item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete work item: {str(e)}")


@backfill_router.get("/status",
                     response_model=WorkQueueStatus,
                     operation_id="getBackfillWorkQueueStatus")
def get_work_queue_status(session_name: str):
    """Get the status of the backfill work queue for a session."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        status = backfill_work_db.get_work_queue_status(session_name)
        return status
        
    except Exception as e:
        logger.error(f"Failed to get work queue status for session {session_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get work queue status: {str(e)}")


@backfill_router.get("/",
                     response_model=List[BackfillWorkItem],
                     operation_id="listBackfillWorkItems")
def list_work_items(session_name: str):
    """List all work items for a session."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        work_items = backfill_work_db.list_work_items_by_session(session_name)
        return work_items
        
    except Exception as e:
        logger.error(f"Failed to list work items for session {session_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list work items: {str(e)}")


@backfill_router.get("/{work_item_id}",
                     response_model=BackfillWorkItem,
                     operation_id="getBackfillWorkItem")
def get_work_item(session_name: str, work_item_id: str):
    """Get a specific work item."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        work_item = backfill_work_db.find_work_item(session_name, work_item_id)
        
        if not work_item:
            raise HTTPException(status_code=404, detail=f"Work item {work_item_id} not found")
        
        return work_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get work item {work_item_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get work item: {str(e)}")


@backfill_router.delete("/",
                        operation_id="deleteAllBackfillWorkItems")
def delete_all_work_items(session_name: str):
    """Delete all work items for a session."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        deleted_count = backfill_work_db.delete_work_items_by_session(session_name)
        logger.info(f"Deleted {deleted_count} work items for session {session_name}")
        
        return {"detail": f"Deleted {deleted_count} work items"}
        
    except Exception as e:
        logger.error(f"Failed to delete work items for session {session_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete work items: {str(e)}")


@backfill_router.post("/cleanup-expired",
                      operation_id="cleanupExpiredBackfillLeases")
def cleanup_expired_leases(session_name: str):
    """Clean up expired leases for a session."""
    # Verify session exists
    http_safe_find_session(session_name)
    
    try:
        cleanup_count = backfill_work_db.cleanup_expired_leases(session_name)
        logger.info(f"Cleaned up {cleanup_count} expired leases for session {session_name}")
        
        return {"detail": f"Cleaned up {cleanup_count} expired leases"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired leases for session {session_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired leases: {str(e)}")
