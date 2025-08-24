import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from console_link.services.snapshot_service import SnapshotService
from console_link.domain.entities.snapshot_entity import SnapshotEntity, SnapshotState, SnapshotType
from console_link.domain.entities.cluster_entity import ClusterEntity, ClusterRole
from console_link.domain.value_objects.snapshot_config import SnapshotConfig
from console_link.domain.value_objects.auth_config import BasicAuthConfig
from console_link.domain.value_objects.s3_config import S3Config
from console_link.domain.exceptions.snapshot_errors import (
    SnapshotCreationError,
    SnapshotNotFoundError,
    SnapshotDeletionError,
    SnapshotValidationError
)
from console_link.models.cluster import Cluster, HttpMethod
from console_link.models.command_runner import CommandRunner, CommandRunnerError


class TestSnapshotService:
    """Unit tests for SnapshotService."""

    @pytest.fixture
    def mock_command_runner(self):
        """Mock command runner."""
        mock = Mock(spec=CommandRunner)
        return mock

    @pytest.fixture
    def mock_cluster_api_client(self):
        """Mock cluster API client."""
        return Mock()

    @pytest.fixture
    def source_cluster_entity(self):
        """Test source cluster entity."""
        return ClusterEntity(
            endpoint="https://source.example.com:9200",
            role=ClusterRole.SOURCE,
            name="source-cluster",
            allow_insecure=False,
            auth_config=BasicAuthConfig(
                username="admin",
                password="admin123"
            )
        )

    @pytest.fixture
    def source_cluster(self):
        """Test source cluster (legacy model)."""
        mock_cluster = Mock(spec=Cluster)
        mock_cluster.call_api = Mock()
        return mock_cluster

    @pytest.fixture
    def snapshot_config(self):
        """Test snapshot configuration."""
        return SnapshotConfig(
            snapshot_name="test-snapshot",
            snapshot_repo_name="test-repo",
            otel_endpoint="http://localhost:4317"
        )

    @pytest.fixture
    def s3_config(self):
        """Test S3 configuration."""
        return S3Config(
            repo_uri="s3://test-bucket/snapshots",
            region="us-east-1",
            role_arn="arn:aws:iam::123456789012:role/SnapshotRole",
            endpoint=None
        )

    @pytest.fixture
    def snapshot_service(self, mock_command_runner, mock_cluster_api_client):
        """Create SnapshotService instance."""
        # Mock the CommandRunner class itself
        with patch('console_link.services.snapshot_service.CommandRunner', return_value=mock_command_runner):
            return SnapshotService(
                command_runner=lambda *args, **kwargs: mock_command_runner,
                cluster_api_client=mock_cluster_api_client
            )

    def test_create_s3_snapshot_success(self, snapshot_service, mock_command_runner, snapshot_config, s3_config, source_cluster_entity):
        """Test successful S3 snapshot creation."""
        # Arrange
        mock_command_runner.run.return_value = None  # Successful execution

        # Act
        result = snapshot_service.create_s3_snapshot(
            config=snapshot_config,
            s3_config=s3_config,
            source_cluster=source_cluster_entity,
            wait=False
        )

        # Assert
        assert isinstance(result, SnapshotEntity)
        assert result.name == "test-snapshot"
        assert result.repository_name == "test-repo"
        assert result.type == SnapshotType.S3
        assert result.state == SnapshotState.IN_PROGRESS
        assert result.s3_uri == "s3://test-bucket/snapshots"
        mock_command_runner.run.assert_called_once()

    def test_create_s3_snapshot_validation_error(self, snapshot_service, snapshot_config, s3_config):
        """Test S3 snapshot creation with missing source cluster."""
        # Act & Assert
        with pytest.raises(SnapshotValidationError) as exc_info:
            snapshot_service.create_s3_snapshot(
                config=snapshot_config,
                s3_config=s3_config,
                source_cluster=None  # Missing source cluster
            )
        
        assert "Source cluster is required" in str(exc_info.value)

    def test_create_s3_snapshot_command_failure(self, snapshot_service, mock_command_runner, snapshot_config, s3_config, source_cluster_entity):
        """Test S3 snapshot creation when command fails."""
        # Arrange
        mock_command_runner.run.side_effect = CommandRunnerError(1, ["test_command"], "Repository not found")

        # Act & Assert
        with pytest.raises(SnapshotCreationError) as exc_info:
            snapshot_service.create_s3_snapshot(
                config=snapshot_config,
                s3_config=s3_config,
                source_cluster=source_cluster_entity
            )
        
        assert "Repository not found" in str(exc_info.value)

    def test_get_snapshot_status_success(self, snapshot_service, source_cluster):
        """Test getting snapshot status successfully."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'snapshots': [{
                'snapshot': 'test-snapshot',
                'uuid': 'snap-12345',
                'state': 'IN_PROGRESS',
                'start_time_in_millis': 1640000000000,
                'shards': {
                    'total': 5,
                    'successful': 3,
                    'failed': 0
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        source_cluster.call_api.return_value = mock_response

        # Act
        result = snapshot_service.get_snapshot_status("test-snapshot", "test-repo", source_cluster)

        # Assert
        assert isinstance(result, dict)
        assert result['state'] == 'IN_PROGRESS'
        assert result['snapshot_info']['snapshot'] == 'test-snapshot'
        source_cluster.call_api.assert_called_with('/_snapshot/test-repo/test-snapshot', HttpMethod.GET)

    def test_get_snapshot_status_not_found(self, snapshot_service, source_cluster):
        """Test getting status of non-existent snapshot."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'snapshots': []
        }
        mock_response.raise_for_status = Mock()
        source_cluster.call_api.return_value = mock_response

        # Act & Assert
        with pytest.raises(SnapshotNotFoundError) as exc_info:
            snapshot_service.get_snapshot_status("non-existent", "test-repo", source_cluster)
        
        assert "Snapshot non-existent not found" in str(exc_info.value)

    def test_delete_all_snapshots_success(self, snapshot_service, source_cluster):
        """Test deleting all snapshots successfully."""
        # Arrange
        list_response = Mock()
        list_response.json.return_value = {
            'snapshots': [
                {
                    'snapshot': 'snapshot-1',
                    'uuid': 'snap-1',
                    'state': 'SUCCESS'
                },
                {
                    'snapshot': 'snapshot-2',
                    'uuid': 'snap-2',
                    'state': 'SUCCESS'
                }
            ]
        }
        list_response.raise_for_status = Mock()
        
        delete_response = Mock()
        delete_response.raise_for_status = Mock()
        
        source_cluster.call_api.side_effect = [list_response, delete_response, delete_response]

        # Act
        result = snapshot_service.delete_all_snapshots("test-repo", source_cluster)

        # Assert
        assert len(result) == 2
        assert 'snapshot-1' in result
        assert 'snapshot-2' in result

    def test_delete_snapshot_success(self, snapshot_service, source_cluster):
        """Test deleting snapshot successfully."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        source_cluster.call_api.return_value = mock_response

        # Act - No return value for delete_snapshot
        snapshot_service.delete_snapshot("test-snapshot", "test-repo", source_cluster)

        # Assert
        source_cluster.call_api.assert_called_once_with('/_snapshot/test-repo/test-snapshot', HttpMethod.DELETE)

    def test_delete_snapshot_failure(self, snapshot_service, source_cluster):
        """Test failed snapshot deletion."""
        # Arrange
        source_cluster.call_api.side_effect = Exception("Connection refused")

        # Act & Assert
        with pytest.raises(SnapshotDeletionError) as exc_info:
            snapshot_service.delete_snapshot("test-snapshot", "test-repo", source_cluster)
        
        assert "Failed to delete snapshot" in str(exc_info.value)

    def test_create_filesystem_snapshot_success(self, snapshot_service, mock_command_runner, snapshot_config, source_cluster_entity):
        """Test successful filesystem snapshot creation."""
        # Arrange
        mock_command_runner.run.return_value = None  # Successful execution
        repo_path = "/mnt/snapshots"

        # Act
        result = snapshot_service.create_filesystem_snapshot(
            config=snapshot_config,
            repo_path=repo_path,
            source_cluster=source_cluster_entity
        )

        # Assert
        assert isinstance(result, SnapshotEntity)
        assert result.name == "test-snapshot"
        assert result.repository_name == "test-repo"
        assert result.type == SnapshotType.FILESYSTEM
        assert result.state == SnapshotState.IN_PROGRESS
        assert result.filesystem_path == repo_path
        mock_command_runner.run.assert_called_once()

    def test_create_filesystem_snapshot_validation_error(self, snapshot_service, snapshot_config, source_cluster_entity):
        """Test filesystem snapshot creation with empty repo path."""
        # Act & Assert
        with pytest.raises(SnapshotValidationError) as exc_info:
            snapshot_service.create_filesystem_snapshot(
                config=snapshot_config,
                repo_path="",  # Empty path
                source_cluster=source_cluster_entity
            )
        
        assert "Repository path is required" in str(exc_info.value)

    def test_get_snapshot_status_deep_check(self, snapshot_service, source_cluster):
        """Test getting detailed snapshot status with deep check."""
        # Arrange
        basic_response = Mock()
        basic_response.json.return_value = {
            'snapshots': [{
                'snapshot': 'test-snapshot',
                'uuid': 'snap-12345',
                'state': 'IN_PROGRESS'
            }]
        }
        basic_response.raise_for_status = Mock()
        
        detailed_response = Mock()
        detailed_response.json.return_value = {
            'snapshots': [{
                'snapshot': 'test-snapshot',
                'uuid': 'snap-12345',
                'state': 'IN_PROGRESS',
                'indices_details': {...}  # Detailed info
            }]
        }
        detailed_response.raise_for_status = Mock()
        
        source_cluster.call_api.side_effect = [basic_response, detailed_response]

        # Act
        result = snapshot_service.get_snapshot_status("test-snapshot", "test-repo", source_cluster, deep_check=True)

        # Assert
        assert result['state'] == 'IN_PROGRESS'
        assert 'detailed_status' in result
        assert source_cluster.call_api.call_count == 2

    def test_delete_snapshot_repository_success(self, snapshot_service, source_cluster):
        """Test deleting snapshot repository successfully."""
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        source_cluster.call_api.return_value = mock_response

        # Act
        snapshot_service.delete_snapshot_repository("test-repo", source_cluster)

        # Assert
        source_cluster.call_api.assert_called_once_with('/_snapshot/test-repo', method=HttpMethod.DELETE)
