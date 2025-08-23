"""Backfill service for managing backfill operations.

This service implements business logic for backfill operations including
starting, stopping, monitoring progress, and scaling.
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from console_link.domain.entities.backfill_entity import BackfillEntity, BackfillType, BackfillStatus, BackfillState
from console_link.domain.exceptions.backfill_errors import (
    BackfillCreationError,
    BackfillNotFoundError,
    BackfillValidationError,
    BackfillWorkCoordinationError,
    BackfillAlreadyRunningError,
    BackfillNotRunningError,
    BackfillStopError,
    BackfillStatusError,
    BackfillScaleError,
)
from console_link.domain.value_objects.container_config import ContainerConfig
# Temporary imports - will be replaced when infrastructure layer is implemented
# from console_link.infrastructure.backfill_executor import BackfillExecutor
from console_link.models.command_runner import CommandRunner, CommandRunnerError
from console_link.models.utils import ExitCode

logger = logging.getLogger(__name__)


class BackfillService:
    """Service for managing backfill operations."""

    def __init__(self, environment=None, command_runner=None, work_coordinator=None):
        """Initialize the backfill service.
        
        Args:
            environment: Environment configuration
            command_runner: Optional command runner for executing system commands
            work_coordinator: Optional work coordinator for managing distributed work
        """
        self.environment = environment
        self.command_runner = command_runner or CommandRunner
        self.work_coordinator = work_coordinator

    def create_backfill(
        self,
        backfill_type: BackfillType,
        config: Dict[str, Any],
        container_config: Optional[ContainerConfig] = None,
    ) -> BackfillEntity:
        """Create a new backfill operation.
        
        Args:
            backfill_type: Type of backfill operation
            config: Backfill configuration
            container_config: Container runtime configuration
            
        Returns:
            BackfillEntity representing the backfill
            
        Raises:
            BackfillValidationError: If configuration is invalid
            BackfillCreationError: If backfill creation fails
        """
        # Validate inputs
        if not config:
            raise BackfillValidationError("Backfill configuration is required")
        
        # Generate backfill ID based on type and timestamp
        backfill_id = f"{backfill_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backfill entity
        backfill = BackfillEntity(
            id=backfill_id,
            type=backfill_type,
            status=BackfillStatus.NOT_STARTED,
            state=BackfillState.PENDING,
            config=config,
            scale_units=config.get("scale", 1),
        )
        
        # Initialize shards if provided in config
        if "shard_total" in config:
            backfill.shard_total = config["shard_total"]
            backfill.shard_complete = 0
            backfill.shard_failed = 0
            backfill.shard_in_progress = 0
            backfill.shard_waiting = config["shard_total"]
        
        return backfill

    def start_backfill(
        self,
        backfill: BackfillEntity,
        wait: bool = False,
        extra_args: Optional[List[str]] = None,
    ) -> BackfillEntity:
        """Start a backfill operation.
        
        Args:
            backfill: Backfill entity to start
            wait: Whether to wait for backfill completion
            extra_args: Additional command arguments
            
        Returns:
            Updated BackfillEntity
            
        Raises:
            BackfillAlreadyRunningError: If backfill is already running
            BackfillCreationError: If start operation fails
        """
        # Check if backfill can be started
        if not backfill.can_start:
            raise BackfillAlreadyRunningError(
                f"Backfill {backfill.id} cannot be started from status {backfill.status.value}"
            )
        
        try:
            # Create appropriate backfill implementation
            if backfill.type == BackfillType.OPENSEARCH_INGESTION:
                backfill_impl = self._create_osi_backfill(backfill)
            elif backfill.type == BackfillType.REINDEX_FROM_SNAPSHOT:
                backfill_impl = self._create_rfs_backfill(backfill)
            else:
                raise BackfillCreationError(f"Unknown backfill type: {backfill.type}")
            
            # Start the backfill
            result = backfill_impl.start(wait=wait, extra_args=extra_args)
            
            # Update backfill state
            backfill.start()
            
            logger.info(f"Backfill {backfill.id} started successfully")
            return backfill
            
        except CommandRunnerError as e:
            backfill.fail(f"Failed to start backfill: {str(e)}")
            logger.error(f"Failed to start backfill {backfill.id}: {str(e)}")
            raise BackfillCreationError(f"Failed to start backfill: {str(e)}")
        except Exception as e:
            backfill.fail(f"Unexpected error starting backfill: {str(e)}")
            logger.error(f"Unexpected error starting backfill {backfill.id}: {str(e)}")
            raise BackfillCreationError(f"Unexpected error starting backfill: {str(e)}")

    def stop_backfill(self, backfill: BackfillEntity) -> BackfillEntity:
        """Stop a running backfill operation.
        
        Args:
            backfill: Backfill entity to stop
            
        Returns:
            Updated BackfillEntity
            
        Raises:
            BackfillNotRunningError: If backfill is not running
            BackfillStopError: If stop operation fails
        """
        # Check if backfill can be stopped
        if not backfill.can_stop:
            raise BackfillNotRunningError(
                f"Backfill {backfill.id} cannot be stopped from status {backfill.status.value}"
            )
        
        try:
            # Create appropriate backfill implementation
            if backfill.type == BackfillType.OPENSEARCH_INGESTION:
                backfill_impl = self._create_osi_backfill(backfill)
            elif backfill.type == BackfillType.REINDEX_FROM_SNAPSHOT:
                backfill_impl = self._create_rfs_backfill(backfill)
            else:
                raise BackfillStopError(f"Unknown backfill type: {backfill.type}")
            
            # Stop the backfill
            result = backfill_impl.stop()
            
            # Update backfill state
            backfill.stop()
            
            logger.info(f"Backfill {backfill.id} stopped successfully")
            return backfill
            
        except CommandRunnerError as e:
            logger.error(f"Failed to stop backfill {backfill.id}: {str(e)}")
            raise BackfillStopError(f"Failed to stop backfill: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error stopping backfill {backfill.id}: {str(e)}")
            raise BackfillStopError(f"Unexpected error stopping backfill: {str(e)}")

    def get_backfill_status(self, backfill: BackfillEntity) -> Dict[str, Any]:
        """Get the status of a backfill operation.
        
        Args:
            backfill: Backfill entity
            
        Returns:
            Dict containing backfill status information
            
        Raises:
            BackfillStatusError: If status retrieval fails
        """
        try:
            # Create appropriate backfill implementation
            if backfill.type == BackfillType.OPENSEARCH_INGESTION:
                backfill_impl = self._create_osi_backfill(backfill)
            elif backfill.type == BackfillType.REINDEX_FROM_SNAPSHOT:
                backfill_impl = self._create_rfs_backfill(backfill)
            else:
                raise BackfillStatusError(f"Unknown backfill type: {backfill.type}")
            
            # Get status
            result = backfill_impl.get_status(deep_check=True)
            
            # Parse status and update entity
            if "shards" in result.value:
                shards_info = result.value["shards"]
                backfill.update_progress(
                    percentage=result.value.get("percent_completed", 0),
                    shard_complete=shards_info.get("completed", 0),
                    shard_in_progress=shards_info.get("in_progress", 0),
                    shard_waiting=shards_info.get("pending", 0),
                    eta_ms=result.value.get("eta_millis"),
                )
            
            # Update status based on result
            if result.value.get("running", False):
                backfill.status = BackfillStatus.RUNNING
                backfill.state = BackfillState.RUNNING
            elif result.value.get("percent_completed", 0) >= 100:
                backfill.complete()
            
            return result.value
            
        except Exception as e:
            logger.error(f"Failed to get status for backfill {backfill.id}: {str(e)}")
            raise BackfillStatusError(f"Failed to get backfill status: {str(e)}")

    def scale_backfill(self, backfill: BackfillEntity, units: int) -> BackfillEntity:
        """Scale a backfill operation.
        
        Args:
            backfill: Backfill entity to scale
            units: Number of scale units
            
        Returns:
            Updated BackfillEntity
            
        Raises:
            BackfillValidationError: If scale units are invalid
            BackfillScaleError: If scaling fails
        """
        if units < 0:
            raise BackfillValidationError("Scale units must be non-negative")
        
        if not backfill.is_running:
            raise BackfillScaleError("Can only scale running backfills")
        
        try:
            # Create appropriate backfill implementation
            if backfill.type == BackfillType.OPENSEARCH_INGESTION:
                backfill_impl = self._create_osi_backfill(backfill)
            elif backfill.type == BackfillType.REINDEX_FROM_SNAPSHOT:
                backfill_impl = self._create_rfs_backfill(backfill)
            else:
                raise BackfillScaleError(f"Unknown backfill type: {backfill.type}")
            
            # Scale the backfill
            result = backfill_impl.scale(units)
            
            # Update backfill scale
            backfill.scale(units)
            
            logger.info(f"Backfill {backfill.id} scaled to {units} units")
            return backfill
            
        except Exception as e:
            logger.error(f"Failed to scale backfill {backfill.id}: {str(e)}")
            raise BackfillScaleError(f"Failed to scale backfill: {str(e)}")

    def get_work_items(self, backfill: BackfillEntity) -> List[Dict[str, Any]]:
        """Get work items for a backfill operation.
        
        Args:
            backfill: Backfill entity
            
        Returns:
            List of work items
            
        Raises:
            BackfillWorkCoordinationError: If work item retrieval fails
        """
        if not self.work_coordinator:
            raise BackfillWorkCoordinationError("Work coordinator not configured")
        
        try:
            work_items = self.work_coordinator.get_work_items(backfill.id)
            return work_items
        except Exception as e:
            logger.error(f"Failed to get work items for backfill {backfill.id}: {str(e)}")
            raise BackfillWorkCoordinationError(f"Failed to get work items: {str(e)}")

    def update_work_item(
        self,
        backfill: BackfillEntity,
        work_item_id: str,
        status: str,
        lease_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update a work item status.
        
        Args:
            backfill: Backfill entity
            work_item_id: Work item ID
            status: New status
            lease_duration: Optional lease duration in seconds
            
        Returns:
            Updated work item
            
        Raises:
            BackfillWorkCoordinationError: If work item update fails
        """
        if not self.work_coordinator:
            raise BackfillWorkCoordinationError("Work coordinator not configured")
        
        try:
            updated_item = self.work_coordinator.update_work_item(
                backfill.id,
                work_item_id,
                status,
                lease_duration
            )
            return updated_item
        except Exception as e:
            logger.error(f"Failed to update work item {work_item_id}: {str(e)}")
            raise BackfillWorkCoordinationError(f"Failed to update work item: {str(e)}")

    def _create_osi_backfill(self, backfill: BackfillEntity):
        """Create an OpenSearch Ingestion backfill implementation.
        
        TODO: This will be replaced when the infrastructure layer is implemented.
        """
        # Extract OSI-specific config
        osi_config = backfill.config.get("opensearch_ingestion", {})
        pipeline_arn = osi_config.get("pipeline_arn")
        
        if not pipeline_arn:
            raise BackfillValidationError("OpenSearch Ingestion pipeline ARN is required")
        
        # Temporary placeholder - will be replaced with infrastructure implementation
        raise NotImplementedError("OSI backfill executor not yet implemented in new architecture")

    def _create_rfs_backfill(self, backfill: BackfillEntity):
        """Create a Reindex from Snapshot backfill implementation.
        
        TODO: This will be replaced when the infrastructure layer is implemented.
        """
        # Extract RFS-specific config
        rfs_config = backfill.config.get("reindex_from_snapshot", {})
        
        # Temporary placeholder - will be replaced with infrastructure implementation
        raise NotImplementedError("RFS backfill executor not yet implemented in new architecture")
