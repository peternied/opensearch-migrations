import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from console_link.services.backfill_service import BackfillService
from console_link.domain.entities.backfill_entity import BackfillEntity, BackfillState, BackfillType, BackfillStatus
from console_link.domain.value_objects.container_config import ContainerConfig
from console_link.domain.exceptions.backfill_errors import (
    BackfillCreationError,
    BackfillNotFoundError,
    BackfillValidationError,
    BackfillAlreadyRunningError,
    BackfillNotRunningError,
    BackfillStopError,
    BackfillStatusError,
    BackfillScaleError,
    BackfillWorkCoordinationError
)
from console_link.models.command_runner import CommandRunner, CommandRunnerError
from console_link.models.command_result import CommandResult


class TestBackfillService:
    """Unit tests for BackfillService."""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment."""
        return Mock()

    @pytest.fixture
    def mock_command_runner(self):
        """Mock command runner."""
        return Mock(spec=CommandRunner)

    @pytest.fixture
    def mock_work_coordinator(self):
        """Mock work coordinator."""
        return Mock()

    @pytest.fixture
    def osi_config(self):
        """Test OpenSearch Ingestion configuration."""
        return {
            "opensearch_ingestion": {
                "pipeline_arn": "arn:aws:osis:us-east-1:123456789012:pipeline/test-pipeline",
                "source_endpoint": "https://source.example.com:9200",
                "target_endpoint": "https://target.example.com:9200"
            },
            "shard_total": 10,
            "scale": 2
        }

    @pytest.fixture
    def rfs_config(self):
        """Test Reindex from Snapshot configuration."""
        return {
            "reindex_from_snapshot": {
                "snapshot_name": "test-snapshot",
                "repository_name": "test-repo",
                "source_host": "https://source.example.com:9200",
                "target_host": "https://target.example.com:9200",
                "index_pattern": "*"
            },
            "shard_total": 5
        }

    @pytest.fixture
    def backfill_service(self, mock_environment, mock_command_runner, mock_work_coordinator):
        """Create BackfillService instance."""
        return BackfillService(
            environment=mock_environment,
            command_runner=lambda *args, **kwargs: mock_command_runner,
            work_coordinator=mock_work_coordinator
        )

    def test_create_backfill_osi_success(self, backfill_service, osi_config):
        """Test creating OpenSearch Ingestion backfill successfully."""
        # Act
        result = backfill_service.create_backfill(
            backfill_type=BackfillType.OPENSEARCH_INGESTION,
            config=osi_config
        )

        # Assert
        assert isinstance(result, BackfillEntity)
        assert result.type == BackfillType.OPENSEARCH_INGESTION
        assert result.status == BackfillStatus.NOT_STARTED
        assert result.state == BackfillState.PENDING
        assert result.config == osi_config
        assert result.scale_units == 2
        assert result.shard_total == 10
        assert result.shard_waiting == 10

    def test_create_backfill_rfs_success(self, backfill_service, rfs_config):
        """Test creating Reindex from Snapshot backfill successfully."""
        # Act
        result = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # Assert
        assert isinstance(result, BackfillEntity)
        assert result.type == BackfillType.REINDEX_FROM_SNAPSHOT
        assert result.status == BackfillStatus.NOT_STARTED
        assert result.config == rfs_config
        assert result.scale_units == 1  # Default when not specified
        assert result.shard_total == 5

    def test_create_backfill_validation_error(self, backfill_service):
        """Test creating backfill with invalid config."""
        # Act & Assert
        with pytest.raises(BackfillValidationError) as exc_info:
            backfill_service.create_backfill(
                backfill_type=BackfillType.OPENSEARCH_INGESTION,
                config=None  # Missing config
            )
        
        assert "Backfill configuration is required" in str(exc_info.value)

    def test_start_backfill_osi_not_implemented(self, backfill_service, osi_config):
        """Test starting OSI backfill (not yet implemented)."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.OPENSEARCH_INGESTION,
            config=osi_config
        )

        # Act & Assert
        with pytest.raises(NotImplementedError) as exc_info:
            backfill_service.start_backfill(backfill)
        
        assert "OSI backfill executor not yet implemented" in str(exc_info.value)

    def test_start_backfill_already_running(self, backfill_service, rfs_config):
        """Test starting backfill when already running."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        backfill.status = BackfillStatus.RUNNING  # Already running

        # Act & Assert
        with pytest.raises(BackfillAlreadyRunningError) as exc_info:
            backfill_service.start_backfill(backfill)
        
        assert "cannot be started from status RUNNING" in str(exc_info.value)

    def test_stop_backfill_not_running(self, backfill_service, rfs_config):
        """Test stopping backfill when not running."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        # Backfill is in NOT_STARTED state

        # Act & Assert
        with pytest.raises(BackfillNotRunningError) as exc_info:
            backfill_service.stop_backfill(backfill)
        
        assert "cannot be stopped from status NOT_STARTED" in str(exc_info.value)

    @patch('console_link.services.backfill_service.BackfillService._create_rfs_backfill')
    def test_get_backfill_status_success(self, mock_create_rfs, backfill_service, rfs_config):
        """Test getting backfill status successfully."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        backfill.status = BackfillStatus.RUNNING
        
        mock_backfill_impl = Mock()
        mock_backfill_impl.get_status.return_value = CommandResult(
            success=True,
            value={
                "running": True,
                "percent_completed": 50.0,
                "shards": {
                    "completed": 2,
                    "in_progress": 1,
                    "pending": 2
                },
                "eta_millis": 60000
            }
        )
        mock_create_rfs.return_value = mock_backfill_impl

        # Act
        result = backfill_service.get_backfill_status(backfill)

        # Assert
        assert result["running"] is True
        assert result["percent_completed"] == 50.0
        assert backfill.percentage_completed == 50.0
        assert backfill.shard_complete == 2
        assert backfill.shard_in_progress == 1
        assert backfill.shard_waiting == 2

    def test_get_backfill_status_unknown_type(self, backfill_service):
        """Test getting status for unknown backfill type."""
        # Arrange
        backfill = BackfillEntity(
            id="test-backfill",
            type=Mock()  # Invalid type
        )

        # Act & Assert
        with pytest.raises(BackfillStatusError) as exc_info:
            backfill_service.get_backfill_status(backfill)
        
        assert "Unknown backfill type" in str(exc_info.value)

    def test_scale_backfill_not_running(self, backfill_service, rfs_config):
        """Test scaling backfill when not running."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # Act & Assert
        with pytest.raises(BackfillScaleError) as exc_info:
            backfill_service.scale_backfill(backfill, units=5)
        
        assert "Can only scale running backfills" in str(exc_info.value)

    def test_scale_backfill_invalid_units(self, backfill_service, rfs_config):
        """Test scaling backfill with invalid units."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        backfill.status = BackfillStatus.RUNNING

        # Act & Assert
        with pytest.raises(BackfillValidationError) as exc_info:
            backfill_service.scale_backfill(backfill, units=-1)
        
        assert "Scale units must be non-negative" in str(exc_info.value)

    def test_get_work_items_success(self, backfill_service, mock_work_coordinator, rfs_config):
        """Test getting work items successfully."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        
        mock_work_coordinator.get_work_items.return_value = [
            {"id": "work-1", "status": "pending"},
            {"id": "work-2", "status": "in_progress"}
        ]

        # Act
        result = backfill_service.get_work_items(backfill)

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "work-1"
        mock_work_coordinator.get_work_items.assert_called_once_with(backfill.id)

    def test_get_work_items_no_coordinator(self, backfill_service, rfs_config):
        """Test getting work items without work coordinator."""
        # Arrange
        backfill_service.work_coordinator = None
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # Act & Assert
        with pytest.raises(BackfillWorkCoordinationError) as exc_info:
            backfill_service.get_work_items(backfill)
        
        assert "Work coordinator not configured" in str(exc_info.value)

    def test_update_work_item_success(self, backfill_service, mock_work_coordinator, rfs_config):
        """Test updating work item successfully."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        
        mock_work_coordinator.update_work_item.return_value = {
            "id": "work-1",
            "status": "completed"
        }

        # Act
        result = backfill_service.update_work_item(
            backfill=backfill,
            work_item_id="work-1",
            status="completed",
            lease_duration=300
        )

        # Assert
        assert result["status"] == "completed"
        mock_work_coordinator.update_work_item.assert_called_once_with(
            backfill.id,
            "work-1",
            "completed",
            300
        )

    def test_validate_osi_config_missing_pipeline(self, backfill_service):
        """Test OSI config validation with missing pipeline ARN."""
        # Arrange
        config = {
            "opensearch_ingestion": {
                # Missing pipeline_arn
                "source_endpoint": "https://source.example.com:9200"
            }
        }
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.OPENSEARCH_INGESTION,
            config=config
        )

        # Act & Assert
        with pytest.raises(BackfillValidationError) as exc_info:
            backfill_service._create_osi_backfill(backfill)
        
        assert "OpenSearch Ingestion pipeline ARN is required" in str(exc_info.value)

    def test_backfill_entity_lifecycle(self, backfill_service, rfs_config):
        """Test backfill entity state transitions."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # Test initial state
        assert backfill.status == BackfillStatus.NOT_STARTED
        assert backfill.can_start is True
        assert backfill.can_stop is False

        # Start backfill
        backfill.start()
        assert backfill.status == BackfillStatus.RUNNING
        assert backfill.is_running is True
        assert backfill.can_start is False
        assert backfill.can_stop is True
        assert backfill.started_at is not None

        # Complete backfill
        backfill.complete()
        assert backfill.status == BackfillStatus.COMPLETED
        assert backfill.is_complete is True
        assert backfill.percentage_completed == 100.0
        assert backfill.finished_at is not None

    def test_backfill_entity_fail_state(self, backfill_service, rfs_config):
        """Test backfill entity failure state."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # Start and fail backfill
        backfill.start()
        backfill.fail("Connection timeout")

        # Assert
        assert backfill.status == BackfillStatus.FAILED
        assert backfill.is_failed is True
        assert backfill.error_message == "Connection timeout"
        assert backfill.finished_at is not None

    def test_backfill_entity_progress_update(self, backfill_service, rfs_config):
        """Test updating backfill progress."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )
        backfill.start()

        # Act
        backfill.update_progress(
            percentage=75.0,
            shard_complete=3,
            shard_in_progress=1,
            shard_waiting=1,
            eta_ms=30000
        )

        # Assert
        assert backfill.percentage_completed == 75.0
        assert backfill.shard_complete == 3
        assert backfill.shard_in_progress == 1
        assert backfill.shard_waiting == 1
        assert backfill.eta_ms == 30000

    def test_backfill_entity_scale(self, backfill_service, rfs_config):
        """Test scaling backfill entity."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # Act
        backfill.scale(10)

        # Assert
        assert backfill.scale_units == 10

        # Test invalid scale
        with pytest.raises(BackfillValidationError) as exc_info:
            backfill.scale(-5)
        
        assert "Scale units must be non-negative" in str(exc_info.value)

    def test_backfill_entity_duration(self, backfill_service, rfs_config):
        """Test calculating backfill duration."""
        # Arrange
        backfill = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=rfs_config
        )

        # No start time
        assert backfill.duration_ms is None

        # Start backfill
        backfill.start()
        assert backfill.duration_ms is not None
        assert backfill.duration_ms >= 0

    def test_create_backfill_id_generation(self, backfill_service, osi_config):
        """Test backfill ID generation."""
        # Act
        backfill1 = backfill_service.create_backfill(
            backfill_type=BackfillType.OPENSEARCH_INGESTION,
            config=osi_config
        )
        backfill2 = backfill_service.create_backfill(
            backfill_type=BackfillType.REINDEX_FROM_SNAPSHOT,
            config=osi_config
        )

        # Assert
        assert backfill1.id.startswith("opensearch_ingestion_")
        assert backfill2.id.startswith("reindex_from_snapshot_")
        assert backfill1.id != backfill2.id
