import pytest
from unittest.mock import Mock, patch

from console_link.services.snapshot_service import SnapshotService
from console_link.services.cluster_service import ClusterService
from console_link.services.backfill_service import BackfillService
from console_link.domain.entities.snapshot_entity import SnapshotEntity, SnapshotState, SnapshotType
from console_link.domain.entities.cluster_entity import ClusterEntity, ClusterRole
from console_link.domain.entities.backfill_entity import BackfillEntity, BackfillType, BackfillStatus
from console_link.domain.value_objects.snapshot_config import SnapshotConfig
from console_link.domain.value_objects.s3_config import S3Config
from console_link.domain.value_objects.auth_config import BasicAuthConfig


class TestServiceIntegration:
    """Integration tests for the refactored services."""

    def test_snapshot_entity_creation(self):
        """Test creating a snapshot entity."""
        snapshot = SnapshotEntity(
            name="test-snapshot",
            repository_name="test-repo",
            type=SnapshotType.S3,
            state=SnapshotState.PENDING,
            s3_uri="s3://test-bucket/snapshots",
            s3_region="us-east-1"
        )
        
        assert snapshot.name == "test-snapshot"
        assert snapshot.is_complete() is False
        assert snapshot.is_in_progress() is False
        
        # Test state transitions
        snapshot.mark_as_started()
        assert snapshot.state == SnapshotState.IN_PROGRESS
        assert snapshot.is_in_progress() is True
        
        snapshot.mark_as_completed()
        assert snapshot.state == SnapshotState.SUCCESS
        assert snapshot.is_complete() is True

    def test_cluster_entity_creation(self):
        """Test creating a cluster entity."""
        cluster = ClusterEntity(
            endpoint="https://test-cluster:9200",
            role=ClusterRole.SOURCE,
            name="test-cluster",
            auth_config=BasicAuthConfig(
                username="admin",
                password="admin123"
            )
        )
        
        assert cluster.endpoint == "https://test-cluster:9200"
        assert cluster.is_source is True
        assert cluster.is_target is False
        assert cluster.is_secure is True
        
        # Test serialization
        cluster_dict = cluster.to_dict()
        assert cluster_dict["endpoint"] == "https://test-cluster:9200"
        assert cluster_dict["role"] == "source"
        assert cluster_dict["auth_config"]["auth_method"] == "basic_auth"

    def test_backfill_entity_lifecycle(self):
        """Test backfill entity lifecycle."""
        backfill = BackfillEntity(
            id="test-backfill-001",
            type=BackfillType.OPENSEARCH_INGESTION,
            config={
                "opensearch_ingestion": {
                    "pipeline_arn": "arn:aws:osis:us-east-1:123456789012:pipeline/test"
                }
            }
        )
        
        assert backfill.id == "test-backfill-001"
        assert backfill.can_start is True
        assert backfill.is_running is False
        
        # Start the backfill
        backfill.start()
        assert backfill.status == BackfillStatus.RUNNING
        assert backfill.is_running is True
        assert backfill.can_stop is True
        
        # Update progress
        backfill.update_progress(
            percentage=50.0,
            shard_complete=5,
            shard_in_progress=2,
            shard_waiting=3
        )
        assert backfill.percentage_completed == 50.0
        
        # Complete the backfill
        backfill.complete()
        assert backfill.is_complete is True
        assert backfill.percentage_completed == 100.0

    @patch('console_link.services.snapshot_service.CommandRunner')
    def test_snapshot_service_initialization(self, mock_command_runner):
        """Test snapshot service can be initialized."""
        service = SnapshotService()
        assert service is not None
        assert service.command_runner is not None

    def test_cluster_service_initialization(self):
        """Test cluster service can be initialized."""
        service = ClusterService()
        assert service is not None

    def test_backfill_service_initialization(self):
        """Test backfill service can be initialized."""
        service = BackfillService()
        assert service is not None
        assert service.command_runner is not None

    def test_value_object_immutability(self):
        """Test that value objects are immutable."""
        s3_config = S3Config(
            repo_uri="s3://test-bucket/snapshots",
            region="us-east-1"
        )
        
        # Value objects should be frozen
        with pytest.raises(AttributeError):
            s3_config.region = "us-west-2"

    def test_domain_exception_hierarchy(self):
        """Test domain exceptions are properly structured."""
        from console_link.domain.exceptions.snapshot_errors import (
            SnapshotError,
            SnapshotCreationError,
            SnapshotValidationError
        )
        from console_link.domain.exceptions.common_errors import (
            MigrationAssistantError,
            ValidationError
        )
        
        # Test inheritance
        assert issubclass(SnapshotError, MigrationAssistantError)
        assert issubclass(SnapshotCreationError, SnapshotError)
        assert issubclass(SnapshotValidationError, SnapshotError)
        assert issubclass(SnapshotValidationError, ValidationError)

    def test_snapshot_config_value_object(self):
        """Test snapshot configuration value object."""
        config = SnapshotConfig(
            snapshot_name="test-snapshot",
            snapshot_repo_name="test-repo",
            otel_endpoint="http://localhost:4317"
        )
        
        assert config.snapshot_name == "test-snapshot"
        assert config.snapshot_repo_name == "test-repo"
        
        # Test immutability
        with pytest.raises(AttributeError):
            config.snapshot_name = "new-name"

    def test_entity_validation(self):
        """Test entity validation works correctly."""
        from console_link.domain.exceptions.snapshot_errors import SnapshotValidationError
        
        # Test invalid snapshot entity
        with pytest.raises(SnapshotValidationError) as exc_info:
            SnapshotEntity(
                name="",  # Empty name should fail
                repository_name="test-repo",
                type=SnapshotType.S3
            )
        assert "Snapshot name cannot be empty" in str(exc_info.value)
        
        # Test invalid percentage
        snapshot = SnapshotEntity(
            name="test",
            repository_name="repo",
            type=SnapshotType.S3,
            s3_uri="s3://test-bucket/snapshots",
            s3_region="us-east-1"
        )
        with pytest.raises(SnapshotValidationError):
            snapshot.percentage_completed = 150  # Over 100 should fail
            snapshot._validate()

    def test_backfill_service_create_backfill(self):
        """Test creating a backfill through the service."""
        service = BackfillService()
        
        config = {
            "opensearch_ingestion": {
                "pipeline_arn": "arn:aws:osis:us-east-1:123456789012:pipeline/test"
            },
            "shard_total": 10,
            "scale": 2
        }
        
        backfill = service.create_backfill(
            backfill_type=BackfillType.OPENSEARCH_INGESTION,
            config=config
        )
        
        assert backfill.type == BackfillType.OPENSEARCH_INGESTION
        assert backfill.scale_units == 2
        assert backfill.shard_total == 10
        assert backfill.id.startswith("opensearch_ingestion_")
