import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from console_link.services.cluster_service import ClusterService
from console_link.domain.entities.cluster_entity import ClusterEntity, ClusterRole, ClusterStatus, ClusterType
from console_link.domain.value_objects.auth_config import BasicAuthConfig, NoAuthConfig, SigV4AuthConfig
from console_link.domain.exceptions.cluster_errors import (
    ClusterConnectionError,
    ClusterNotFoundError,
    ClusterValidationError,
    ClusterHealthCheckError
)
from console_link.infrastructure.http_client import HttpClient


class TestClusterService:
    """Unit tests for ClusterService."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client."""
        return Mock(spec=HttpClient)

    @pytest.fixture
    def basic_auth_config(self):
        """Test basic auth configuration."""
        return BasicAuthConfig(
            username="admin",
            password="admin123"
        )

    @pytest.fixture
    def sigv4_auth_config(self):
        """Test SigV4 auth configuration."""
        return SigV4AuthConfig(
            region="us-east-1",
            service="es"
        )

    @pytest.fixture
    def cluster_entity(self, basic_auth_config):
        """Test cluster entity."""
        return ClusterEntity(
            endpoint="https://test-cluster.example.com:9200",
            role=ClusterRole.SOURCE,
            name="test-cluster",
            allow_insecure=False,
            auth_config=basic_auth_config
        )

    @pytest.fixture
    def cluster_service(self, mock_http_client):
        """Create ClusterService instance."""
        return ClusterService(http_client=mock_http_client)

    def test_test_cluster_connection_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test successful cluster connection test."""
        # Arrange
        mock_response = {
            "name": "test-node",
            "cluster_name": "test-cluster",
            "cluster_uuid": "abc123",
            "version": {
                "number": "7.10.2",
                "distribution": "opensearch"
            }
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.test_cluster_connection(cluster_entity)

        # Assert
        assert result is True
        assert cluster_entity.status == ClusterStatus.CONNECTED
        assert cluster_entity.version == "7.10.2"
        mock_http_client.get.assert_called_once()

    def test_test_cluster_connection_failure(self, cluster_service, mock_http_client, cluster_entity):
        """Test failed cluster connection test."""
        # Arrange
        mock_http_client.get.side_effect = Exception("Connection refused")

        # Act
        result = cluster_service.test_cluster_connection(cluster_entity)

        # Assert
        assert result is False
        assert cluster_entity.status == ClusterStatus.UNREACHABLE
        assert "Connection refused" in cluster_entity.health_message

    def test_get_cluster_info_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test getting cluster info successfully."""
        # Arrange
        mock_response = {
            "name": "test-node",
            "cluster_name": "test-cluster",
            "cluster_uuid": "abc123",
            "version": {
                "number": "7.10.2",
                "distribution": "opensearch",
                "build_type": "tar"
            }
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.get_cluster_info(cluster_entity)

        # Assert
        assert result["cluster_name"] == "test-cluster"
        assert result["version"]["number"] == "7.10.2"
        mock_http_client.get.assert_called_with(
            f"{cluster_entity.endpoint}/",
            auth=cluster_entity.auth_config,
            verify=not cluster_entity.allow_insecure
        )

    def test_get_cluster_info_connection_error(self, cluster_service, mock_http_client, cluster_entity):
        """Test cluster info retrieval with connection error."""
        # Arrange
        mock_http_client.get.side_effect = Exception("Connection timeout")

        # Act & Assert
        with pytest.raises(ClusterConnectionError) as exc_info:
            cluster_service.get_cluster_info(cluster_entity)
        
        assert "Failed to connect to cluster" in str(exc_info.value)

    def test_check_cluster_health_healthy(self, cluster_service, mock_http_client, cluster_entity):
        """Test checking health of a healthy cluster."""
        # Arrange
        mock_response = {
            "cluster_name": "test-cluster",
            "status": "green",
            "number_of_nodes": 3,
            "number_of_data_nodes": 3,
            "active_primary_shards": 10,
            "active_shards": 20,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.check_cluster_health(cluster_entity)

        # Assert
        assert result["status"] == "green"
        assert cluster_entity.status == ClusterStatus.HEALTHY
        assert cluster_entity.node_count == 3
        mock_http_client.get.assert_called_with(
            f"{cluster_entity.endpoint}/_cluster/health",
            auth=cluster_entity.auth_config,
            verify=not cluster_entity.allow_insecure
        )

    def test_check_cluster_health_unhealthy(self, cluster_service, mock_http_client, cluster_entity):
        """Test checking health of an unhealthy cluster."""
        # Arrange
        mock_response = {
            "cluster_name": "test-cluster",
            "status": "red",
            "number_of_nodes": 2,
            "unassigned_shards": 5
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.check_cluster_health(cluster_entity)

        # Assert
        assert result["status"] == "red"
        assert cluster_entity.status == ClusterStatus.UNHEALTHY
        assert "red" in cluster_entity.health_message

    def test_get_cluster_stats_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test getting cluster stats successfully."""
        # Arrange
        mock_response = {
            "indices": {
                "count": 10,
                "docs": {
                    "count": 1000000
                },
                "store": {
                    "size_in_bytes": 5368709120
                }
            },
            "nodes": {
                "count": {
                    "total": 3
                }
            }
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.get_cluster_stats(cluster_entity)

        # Assert
        assert result["indices"]["count"] == 10
        assert cluster_entity.index_count == 10
        assert cluster_entity.document_count == 1000000
        assert cluster_entity.total_size_bytes == 5368709120

    def test_list_indices_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test listing indices successfully."""
        # Arrange
        mock_response = {
            "index1": {
                "health": "green",
                "status": "open",
                "index": "index1",
                "pri": "5",
                "rep": "1",
                "docs.count": "1000",
                "store.size": "5mb"
            },
            "index2": {
                "health": "yellow",
                "status": "open",
                "index": "index2",
                "pri": "3",
                "rep": "1",
                "docs.count": "500",
                "store.size": "2mb"
            }
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.list_indices(cluster_entity)

        # Assert
        assert len(result) == 2
        assert "index1" in result
        assert "index2" in result
        assert result["index1"]["health"] == "green"

    def test_list_indices_with_pattern(self, cluster_service, mock_http_client, cluster_entity):
        """Test listing indices with pattern."""
        # Arrange
        mock_response = {
            "logs-2024-01": {"health": "green"},
            "logs-2024-02": {"health": "green"}
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.list_indices(cluster_entity, pattern="logs-*")

        # Assert
        assert len(result) == 2
        mock_http_client.get.assert_called_with(
            f"{cluster_entity.endpoint}/_cat/indices/logs-*?format=json",
            auth=cluster_entity.auth_config,
            verify=not cluster_entity.allow_insecure
        )

    def test_create_index_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test creating an index successfully."""
        # Arrange
        index_name = "test-index"
        settings = {
            "number_of_shards": 3,
            "number_of_replicas": 1
        }
        mock_http_client.put.return_value = {"acknowledged": True}

        # Act
        result = cluster_service.create_index(cluster_entity, index_name, settings=settings)

        # Assert
        assert result["acknowledged"] is True
        mock_http_client.put.assert_called_with(
            f"{cluster_entity.endpoint}/{index_name}",
            json={"settings": settings},
            auth=cluster_entity.auth_config,
            verify=not cluster_entity.allow_insecure
        )

    def test_delete_index_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test deleting an index successfully."""
        # Arrange
        index_name = "test-index"
        mock_http_client.delete.return_value = {"acknowledged": True}

        # Act
        result = cluster_service.delete_index(cluster_entity, index_name)

        # Assert
        assert result["acknowledged"] is True
        mock_http_client.delete.assert_called_with(
            f"{cluster_entity.endpoint}/{index_name}",
            auth=cluster_entity.auth_config,
            verify=not cluster_entity.allow_insecure
        )

    def test_get_index_mapping_success(self, cluster_service, mock_http_client, cluster_entity):
        """Test getting index mapping successfully."""
        # Arrange
        index_name = "test-index"
        mock_response = {
            "test-index": {
                "mappings": {
                    "properties": {
                        "field1": {"type": "text"},
                        "field2": {"type": "keyword"}
                    }
                }
            }
        }
        mock_http_client.get.return_value = mock_response

        # Act
        result = cluster_service.get_index_mapping(cluster_entity, index_name)

        # Assert
        assert "test-index" in result
        assert result["test-index"]["mappings"]["properties"]["field1"]["type"] == "text"

    def test_cluster_with_no_auth(self, cluster_service, mock_http_client):
        """Test cluster operations with no authentication."""
        # Arrange
        cluster = ClusterEntity(
            endpoint="http://localhost:9200",
            role=ClusterRole.SOURCE,
            auth_config=NoAuthConfig()
        )
        mock_http_client.get.return_value = {"cluster_name": "test"}

        # Act
        result = cluster_service.get_cluster_info(cluster)

        # Assert
        mock_http_client.get.assert_called_with(
            "http://localhost:9200/",
            auth=cluster.auth_config,
            verify=True  # Default when not explicitly set to insecure
        )

    def test_cluster_with_sigv4_auth(self, cluster_service, mock_http_client, sigv4_auth_config):
        """Test cluster operations with SigV4 authentication."""
        # Arrange
        cluster = ClusterEntity(
            endpoint="https://search-domain.us-east-1.es.amazonaws.com",
            role=ClusterRole.TARGET,
            auth_config=sigv4_auth_config
        )
        mock_http_client.get.return_value = {"cluster_name": "aws-cluster"}

        # Act
        result = cluster_service.get_cluster_info(cluster)

        # Assert
        assert result["cluster_name"] == "aws-cluster"
        mock_http_client.get.assert_called_with(
            f"{cluster.endpoint}/",
            auth=sigv4_auth_config,
            verify=True
        )

    def test_validate_cluster_entity_invalid_endpoint(self, cluster_service):
        """Test validation of cluster entity with invalid endpoint."""
        # Act & Assert
        with pytest.raises(ClusterValidationError) as exc_info:
            ClusterEntity(
                endpoint="invalid-endpoint",  # Missing protocol
                role=ClusterRole.SOURCE
            )
        
        assert "must start with http://" in str(exc_info.value)

    def test_compare_cluster_versions(self, cluster_service, mock_http_client):
        """Test comparing versions between source and target clusters."""
        # Arrange
        source_cluster = ClusterEntity(
            endpoint="https://source:9200",
            role=ClusterRole.SOURCE,
            version="7.10.2"
        )
        
        target_cluster = ClusterEntity(
            endpoint="https://target:9200",
            role=ClusterRole.TARGET,
            version="2.11.0"
        )

        # Mock responses for both clusters
        mock_http_client.get.side_effect = [
            {"version": {"number": "7.10.2", "distribution": "elasticsearch"}},
            {"version": {"number": "2.11.0", "distribution": "opensearch"}}
        ]

        # Act
        source_info = cluster_service.get_cluster_info(source_cluster)
        target_info = cluster_service.get_cluster_info(target_cluster)

        # Assert
        assert source_info["version"]["number"] == "7.10.2"
        assert target_info["version"]["number"] == "2.11.0"
        assert source_info["version"]["distribution"] == "elasticsearch"
        assert target_info["version"]["distribution"] == "opensearch"
