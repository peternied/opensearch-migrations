"""FastAPI router for snapshot endpoints."""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime

from console_link.api.schemas.snapshot_schemas import (
    CreateSnapshotRequest,
    SnapshotResponse,
    SnapshotStatusResponse,
    SnapshotListResponse,
    SnapshotRepositoryRequest,
    SnapshotRepositoryResponse,
)
from console_link.api.schemas.error_schemas import (
    ErrorCode,
    ErrorResponse,
    NotFoundErrorResponse,
    ValidationErrorResponse,
)
from console_link.services.snapshot_service import SnapshotService
from console_link.domain.exceptions.snapshot_errors import (
    SnapshotError,
    SnapshotNotFoundError,
    SnapshotCreationError,
    SnapshotValidationError,
    SnapshotInProgressError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/snapshots",
    tags=["snapshots"],
    responses={
        404: {"model": NotFoundErrorResponse, "description": "Snapshot not found"},
        422: {"model": ValidationErrorResponse, "description": "Validation error"},
    },
)


def get_snapshot_service() -> SnapshotService:
    """Dependency to get snapshot service instance."""
    # TODO: Implement proper dependency injection
    # For now, return a singleton or create new instance
    # This will be properly wired up when we integrate with the app
    from console_link.environment import Environment
    from console_link.services.snapshot_service import SnapshotService
    from console_link.infrastructure.command_executor import CommandExecutor
    from console_link.repositories.session_repository import SessionRepository
    
    env = Environment()
    command_executor = CommandExecutor()
    session_repo = SessionRepository()
    
    return SnapshotService(
        command_executor=command_executor,
        session_repository=session_repo,
        environment=env
    )


@router.post(
    "/",
    response_model=SnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new snapshot",
    description="Create a new snapshot in the specified repository"
)
async def create_snapshot(
    request: CreateSnapshotRequest,
    service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotResponse:
    """Create a new snapshot."""
    try:
        entity = service.create_snapshot({
            'snapshot_name': request.snapshot_name,
            'repository_name': request.repository_name,
        })
        return SnapshotResponse.from_entity(entity)
    except SnapshotValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": ErrorCode.VALIDATION_ERROR,
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotInProgressError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": ErrorCode.CONFLICT,
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotError as e:
        logger.error(f"Failed to create snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to create snapshot: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get(
    "/{snapshot_id}",
    response_model=SnapshotResponse,
    summary="Get snapshot details",
    description="Get details of a specific snapshot"
)
async def get_snapshot(
    snapshot_id: str,
    service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotResponse:
    """Get snapshot details."""
    try:
        entity = service.get_snapshot(snapshot_id)
        return SnapshotResponse.from_entity(entity)
    except SnapshotNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": ErrorCode.NOT_FOUND,
                "message": f"Snapshot '{snapshot_id}' not found",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotError as e:
        logger.error(f"Failed to get snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to get snapshot: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get(
    "/{snapshot_id}/status",
    response_model=SnapshotStatusResponse,
    summary="Get snapshot status",
    description="Get the current status of a snapshot"
)
async def get_snapshot_status(
    snapshot_id: str,
    service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotStatusResponse:
    """Get snapshot status."""
    try:
        status_info = service.get_snapshot_status(snapshot_id)
        return SnapshotStatusResponse(
            state=status_info['state'],
            percentage_completed=status_info.get('percentage_completed', 0),
            eta_ms=status_info.get('eta_ms'),
            shards_stats=status_info.get('shards_stats'),
            indices_progress=status_info.get('indices_progress'),
        )
    except SnapshotNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": ErrorCode.NOT_FOUND,
                "message": f"Snapshot '{snapshot_id}' not found",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotError as e:
        logger.error(f"Failed to get snapshot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to get snapshot status: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get(
    "/",
    response_model=SnapshotListResponse,
    summary="List snapshots",
    description="List all snapshots with optional filtering"
)
async def list_snapshots(
    repository: Optional[str] = Query(None, description="Filter by repository name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotListResponse:
    """List snapshots."""
    try:
        entities = service.list_snapshots(
            repository=repository,
            state=state,
            limit=limit,
            offset=offset
        )
        return SnapshotListResponse(
            snapshots=[SnapshotResponse.from_entity(e) for e in entities],
            total=len(entities)  # TODO: Get total count from service
        )
    except SnapshotError as e:
        logger.error(f"Failed to list snapshots: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to list snapshots: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.delete(
    "/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a snapshot",
    description="Delete a specific snapshot"
)
async def delete_snapshot(
    snapshot_id: str,
    service: SnapshotService = Depends(get_snapshot_service)
) -> None:
    """Delete a snapshot."""
    try:
        service.delete_snapshot(snapshot_id)
    except SnapshotNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": ErrorCode.NOT_FOUND,
                "message": f"Snapshot '{snapshot_id}' not found",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotError as e:
        logger.error(f"Failed to delete snapshot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to delete snapshot: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.post(
    "/repositories",
    response_model=SnapshotRepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create snapshot repository",
    description="Create a new snapshot repository"
)
async def create_repository(
    request: SnapshotRepositoryRequest,
    service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotRepositoryResponse:
    """Create a snapshot repository."""
    try:
        result = service.create_repository(
            name=request.name,
            repo_type=request.type.value,
            settings=request.settings
        )
        return SnapshotRepositoryResponse(
            name=result['name'],
            type=request.type,
            settings=result['settings'],
            verified=result.get('verified', False)
        )
    except SnapshotValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": ErrorCode.VALIDATION_ERROR,
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotError as e:
        logger.error(f"Failed to create repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to create repository: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


@router.get(
    "/repositories/{repository_name}",
    response_model=SnapshotRepositoryResponse,
    summary="Get repository details",
    description="Get details of a snapshot repository"
)
async def get_repository(
    repository_name: str,
    service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotRepositoryResponse:
    """Get repository details."""
    try:
        result = service.get_repository(repository_name)
        return SnapshotRepositoryResponse(
            name=result['name'],
            type=result['type'],
            settings=result['settings'],
            verified=result.get('verified', False)
        )
    except SnapshotNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": ErrorCode.NOT_FOUND,
                "message": f"Repository '{repository_name}' not found",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except SnapshotError as e:
        logger.error(f"Failed to get repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": ErrorCode.INTERNAL_ERROR,
                "message": f"Failed to get repository: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
