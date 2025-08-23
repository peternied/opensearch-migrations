"""Cluster service for managing cluster operations.

This service implements business logic for cluster operations including
connection validation, health checks, and metadata operations.
"""

import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from console_link.domain.entities.cluster_entity import ClusterEntity, ClusterRole, ClusterStatus
from console_link.domain.exceptions.cluster_errors import (
    ClusterConnectionError,
    ClusterAuthenticationError,
    ClusterOperationError,
    ClusterValidationError,
)
from console_link.domain.value_objects.auth_config import AuthConfig
from console_link.models.cluster import Cluster as LegacyCluster, HttpMethod
from requests.exceptions import RequestException, HTTPError

logger = logging.getLogger(__name__)


class ClusterService:
    """Service for managing cluster operations."""

    def __init__(self, http_client=None):
        """Initialize the cluster service.
        
        Args:
            http_client: Optional HTTP client for cluster communication
        """
        self.http_client = http_client

    def create_cluster(
        self,
        name: str,
        endpoint: str,
        role: ClusterRole,
        auth_config: Optional[AuthConfig] = None,
        version: Optional[str] = None,
        allow_insecure: bool = False,
    ) -> ClusterEntity:
        """Create a new cluster entity.
        
        Args:
            name: Cluster name
            endpoint: Cluster endpoint URL
            role: Cluster role (SOURCE, TARGET, MONITORING)
            auth_config: Authentication configuration
            version: Cluster version
            allow_insecure: Whether to allow insecure SSL connections
            
        Returns:
            ClusterEntity representing the cluster
            
        Raises:
            ClusterValidationError: If configuration is invalid
        """
        # Validate inputs
        if not name:
            raise ClusterValidationError("Cluster name cannot be empty")
        
        if not endpoint:
            raise ClusterValidationError("Cluster endpoint cannot be empty")
        
        if not self._is_valid_endpoint(endpoint):
            raise ClusterValidationError(f"Invalid endpoint format: {endpoint}")
        
        # Create cluster entity
        cluster = ClusterEntity(
            name=name,
            endpoint=endpoint,
            role=role,
            status=ClusterStatus.UNKNOWN,
            auth_config=auth_config,
            version=version,
            allow_insecure=allow_insecure,
        )
        
        return cluster

    def test_connection(self, cluster: ClusterEntity) -> Dict[str, Any]:
        """Test connection to a cluster.
        
        Args:
            cluster: Cluster entity to test
            
        Returns:
            Dict containing connection test results
            
        Raises:
            ClusterConnectionError: If connection fails
            ClusterAuthenticationError: If authentication fails
        """
        # Convert to legacy cluster for API calls
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        try:
            # Try to get cluster info
            response = legacy_cluster.call_api("/", HttpMethod.GET)
            response.raise_for_status()
            
            cluster_info = response.json()
            
            # Update cluster status
            cluster.status = ClusterStatus.CONNECTED
            cluster.updated_at = datetime.utcnow()
            
            # Extract version if available
            if "version" in cluster_info and "number" in cluster_info["version"]:
                cluster.version = cluster_info["version"]["number"]
            
            return {
                "connected": True,
                "cluster_info": cluster_info,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except HTTPError as e:
            if e.response.status_code == 401:
                cluster.status = ClusterStatus.UNREACHABLE
                cluster.updated_at = datetime.utcnow()
                raise ClusterAuthenticationError(f"Authentication failed for cluster {cluster.name}")
            else:
                cluster.status = ClusterStatus.UNREACHABLE
                cluster.updated_at = datetime.utcnow()
                raise ClusterConnectionError(f"HTTP error connecting to cluster {cluster.name}: {str(e)}")
        except RequestException as e:
            cluster.status = ClusterStatus.UNREACHABLE
            cluster.updated_at = datetime.utcnow()
            raise ClusterConnectionError(f"Failed to connect to cluster {cluster.name}: {str(e)}")
        except Exception as e:
            cluster.status = ClusterStatus.UNREACHABLE
            cluster.updated_at = datetime.utcnow()
            raise ClusterConnectionError(f"Unexpected error connecting to cluster {cluster.name}: {str(e)}")

    def get_cluster_health(self, cluster: ClusterEntity) -> Dict[str, Any]:
        """Get cluster health information.
        
        Args:
            cluster: Cluster entity
            
        Returns:
            Dict containing health information
            
        Raises:
            ClusterOperationError: If health check fails
        """
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        try:
            # Get cluster health
            response = legacy_cluster.call_api("/_cluster/health", HttpMethod.GET)
            response.raise_for_status()
            
            health_data = response.json()
            
            # Update cluster health status
            status_mapping = {
                "green": ClusterStatus.HEALTHY,
                "yellow": ClusterStatus.CONNECTED,
                "red": ClusterStatus.UNHEALTHY,
            }
            health_status = health_data.get("status", "unknown")
            cluster.status = status_mapping.get(health_status, ClusterStatus.UNKNOWN)
            cluster.node_count = health_data.get("number_of_nodes", 0)
            cluster.updated_at = datetime.utcnow()
            
            return health_data
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to get health for cluster {cluster.name}: {str(e)}")

    def get_cluster_stats(self, cluster: ClusterEntity) -> Dict[str, Any]:
        """Get cluster statistics.
        
        Args:
            cluster: Cluster entity
            
        Returns:
            Dict containing cluster statistics
            
        Raises:
            ClusterOperationError: If stats retrieval fails
        """
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        try:
            # Get cluster stats
            response = legacy_cluster.call_api("/_cluster/stats", HttpMethod.GET)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to get stats for cluster {cluster.name}: {str(e)}")

    def get_indices(self, cluster: ClusterEntity, pattern: str = "*") -> List[Dict[str, Any]]:
        """Get list of indices from cluster.
        
        Args:
            cluster: Cluster entity
            pattern: Index pattern to match (default: "*")
            
        Returns:
            List of index information
            
        Raises:
            ClusterOperationError: If index retrieval fails
        """
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        try:
            # Get indices
            response = legacy_cluster.call_api(f"/_cat/indices/{pattern}?format=json", HttpMethod.GET)
            response.raise_for_status()
            
            indices = response.json()
            
            # Update cluster metrics
            cluster.index_count = len(indices)
            cluster.total_size_bytes = sum(int(idx.get("store.size", 0)) for idx in indices if idx.get("store.size"))
            cluster.updated_at = datetime.utcnow()
            
            return indices
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to get indices for cluster {cluster.name}: {str(e)}")

    def get_index_metadata(self, cluster: ClusterEntity, index_name: str) -> Dict[str, Any]:
        """Get metadata for a specific index.
        
        Args:
            cluster: Cluster entity
            index_name: Name of the index
            
        Returns:
            Dict containing index metadata
            
        Raises:
            ClusterOperationError: If metadata retrieval fails
        """
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        try:
            # Get index settings and mappings
            response = legacy_cluster.call_api(f"/{index_name}", HttpMethod.GET)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to get metadata for index {index_name}: {str(e)}")

    def create_index(
        self,
        cluster: ClusterEntity,
        index_name: str,
        settings: Optional[Dict] = None,
        mappings: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a new index.
        
        Args:
            cluster: Cluster entity
            index_name: Name of the index to create
            settings: Index settings
            mappings: Index mappings
            
        Returns:
            Dict containing creation response
            
        Raises:
            ClusterOperationError: If index creation fails
        """
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        body = {}
        if settings:
            body["settings"] = settings
        if mappings:
            body["mappings"] = mappings
        
        try:
            # Create index
            response = legacy_cluster.call_api(
                f"/{index_name}",
                method=HttpMethod.PUT,
                json_body=body if body else None
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to create index {index_name}: {str(e)}")

    def delete_index(self, cluster: ClusterEntity, index_name: str) -> Dict[str, Any]:
        """Delete an index.
        
        Args:
            cluster: Cluster entity
            index_name: Name of the index to delete
            
        Returns:
            Dict containing deletion response
            
        Raises:
            ClusterOperationError: If index deletion fails
        """
        legacy_cluster = self._to_legacy_cluster(cluster)
        
        try:
            # Delete index
            response = legacy_cluster.call_api(f"/{index_name}", method=HttpMethod.DELETE)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to delete index {index_name}: {str(e)}")

    def _is_valid_endpoint(self, endpoint: str) -> bool:
        """Validate endpoint format."""
        return endpoint.startswith(("http://", "https://"))

    def _to_legacy_cluster(self, cluster: ClusterEntity) -> LegacyCluster:
        """Convert ClusterEntity to legacy Cluster for API calls.
        
        This is temporary until we refactor the HTTP client layer.
        """
        return LegacyCluster(cluster.to_dict())
