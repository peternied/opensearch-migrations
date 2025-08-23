"""Snapshot service for managing snapshot operations.

This service implements business logic for creating, managing, and
monitoring snapshots. It raises domain exceptions on errors instead
of returning CommandResult objects.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

from console_link.domain.entities.snapshot_entity import SnapshotEntity, SnapshotState, SnapshotType
from console_link.domain.entities.cluster_entity import ClusterEntity
from console_link.domain.exceptions.snapshot_errors import (
    SnapshotCreationError,
    SnapshotNotFoundError,
    SnapshotDeletionError,
    SnapshotValidationError,
)
from console_link.domain.value_objects.snapshot_config import SnapshotConfig
from console_link.domain.value_objects.s3_config import S3Config
from console_link.models.cluster import Cluster, HttpMethod
from console_link.models.command_runner import CommandRunner, CommandRunnerError, FlagOnlyArgument
from console_link.models.utils import DEFAULT_SNAPSHOT_REPO_NAME
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)


class SnapshotService:
    """Service for managing snapshot operations."""

    def __init__(self, command_runner=None, cluster_api_client=None):
        """Initialize the snapshot service.
        
        Args:
            command_runner: Optional command runner for executing system commands
            cluster_api_client: Optional API client for cluster operations
        """
        self.command_runner = command_runner or CommandRunner
        self.cluster_api_client = cluster_api_client

    def create_s3_snapshot(
        self,
        config: SnapshotConfig,
        s3_config: S3Config,
        source_cluster: ClusterEntity,
        wait: bool = False,
        max_snapshot_rate_mb_per_node: Optional[int] = None,
        extra_args: Optional[List[str]] = None,
    ) -> SnapshotEntity:
        """Create an S3-based snapshot.
        
        Args:
            config: Snapshot configuration
            s3_config: S3 storage configuration
            source_cluster: Source cluster entity
            wait: Whether to wait for snapshot completion
            max_snapshot_rate_mb_per_node: Max snapshot rate limit
            extra_args: Additional command arguments
            
        Returns:
            SnapshotEntity representing the created snapshot
            
        Raises:
            SnapshotValidationError: If configuration is invalid
            SnapshotCreationError: If snapshot creation fails
        """
        # Validate inputs
        if not source_cluster:
            raise SnapshotValidationError("Source cluster is required")
        
        if not s3_config.repo_uri:
            raise SnapshotValidationError("S3 repo URI is required")
        
        # Create snapshot entity
        snapshot = SnapshotEntity(
            name=config.snapshot_name,
            repository_name=config.snapshot_repo_name,
            type=SnapshotType.S3,
            state=SnapshotState.PENDING,
            s3_uri=s3_config.repo_uri,
            s3_region=s3_config.region,
            s3_role_arn=s3_config.role_arn,
            s3_endpoint=s3_config.endpoint,
            otel_endpoint=config.otel_endpoint,
            max_snapshot_rate_mb_per_node=max_snapshot_rate_mb_per_node,
        )
        
        # Build command
        base_command = "/root/createSnapshot/bin/CreateSnapshot"
        command_args = self._build_s3_command_args(config, s3_config, source_cluster, wait, max_snapshot_rate_mb_per_node, extra_args)
        
        # Execute snapshot creation
        try:
            runner = self.command_runner(base_command, command_args, sensitive_fields=["--source-password"])
            runner.run()
            
            # Update snapshot state
            snapshot.mark_as_started()
            
            logger.info(f"Snapshot {config.snapshot_name} creation initiated successfully")
            return snapshot
            
        except CommandRunnerError as e:
            logger.error(f"Failed to create snapshot: {str(e)}")
            raise SnapshotCreationError(f"Failed to create snapshot: {str(e)}")

    def create_filesystem_snapshot(
        self,
        config: SnapshotConfig,
        repo_path: str,
        source_cluster: ClusterEntity,
        max_snapshot_rate_mb_per_node: Optional[int] = None,
        extra_args: Optional[List[str]] = None,
    ) -> SnapshotEntity:
        """Create a filesystem-based snapshot.
        
        Args:
            config: Snapshot configuration
            repo_path: Filesystem repository path
            source_cluster: Source cluster entity
            max_snapshot_rate_mb_per_node: Max snapshot rate limit
            extra_args: Additional command arguments
            
        Returns:
            SnapshotEntity representing the created snapshot
            
        Raises:
            SnapshotValidationError: If configuration is invalid
            SnapshotCreationError: If snapshot creation fails
        """
        # Validate inputs
        if not source_cluster:
            raise SnapshotValidationError("Source cluster is required")
        
        if not repo_path:
            raise SnapshotValidationError("Repository path is required")
        
        # Create snapshot entity
        snapshot = SnapshotEntity(
            name=config.snapshot_name,
            repository_name=config.snapshot_repo_name,
            type=SnapshotType.FILESYSTEM,
            state=SnapshotState.PENDING,
            filesystem_path=repo_path,
            otel_endpoint=config.otel_endpoint,
            max_snapshot_rate_mb_per_node=max_snapshot_rate_mb_per_node,
        )
        
        # Build command
        base_command = "/root/createSnapshot/bin/CreateSnapshot"
        command_args = self._build_filesystem_command_args(config, repo_path, source_cluster, max_snapshot_rate_mb_per_node, extra_args)
        
        # Execute snapshot creation
        try:
            runner = self.command_runner(base_command, command_args, sensitive_fields=["--source-password"])
            runner.run()
            
            # Update snapshot state
            snapshot.mark_as_started()
            
            logger.info(f"Snapshot {config.snapshot_name} creation initiated successfully")
            return snapshot
            
        except CommandRunnerError as e:
            logger.error(f"Failed to create snapshot: {str(e)}")
            raise SnapshotCreationError(f"Failed to create snapshot: {str(e)}")

    def get_snapshot_status(
        self,
        snapshot_name: str,
        repository_name: str,
        source_cluster: Cluster,
        deep_check: bool = False
    ) -> Dict:
        """Get the status of a snapshot.
        
        Args:
            snapshot_name: Name of the snapshot
            repository_name: Repository name
            source_cluster: Source cluster connection
            deep_check: Whether to perform deep status check
            
        Returns:
            Dict containing snapshot status information
            
        Raises:
            SnapshotNotFoundError: If snapshot doesn't exist
            SnapshotCreationError: If status retrieval fails
        """
        try:
            # Get basic snapshot info
            path = f"/_snapshot/{repository_name}/{snapshot_name}"
            response = source_cluster.call_api(path, HttpMethod.GET)
            response.raise_for_status()
            
            snapshot_data = response.json()
            snapshots = snapshot_data.get('snapshots', [])
            
            if not snapshots:
                raise SnapshotNotFoundError(f"Snapshot {snapshot_name} not found in repository {repository_name}")
            
            snapshot_info = snapshots[0]
            state = snapshot_info.get("state")
            
            if not deep_check:
                return {"state": state, "snapshot_info": snapshot_info}
            
            # Get detailed status
            status_path = f"/_snapshot/{repository_name}/{snapshot_name}/_status"
            status_response = source_cluster.call_api(status_path, HttpMethod.GET)
            status_response.raise_for_status()
            
            status_data = status_response.json()
            status_snapshots = status_data.get('snapshots', [])
            
            if not status_snapshots:
                raise SnapshotCreationError("Unable to retrieve detailed snapshot status")
            
            return {
                "state": state,
                "snapshot_info": snapshot_info,
                "detailed_status": status_snapshots[0]
            }
            
        except HTTPError as e:
            if e.response.status_code == 404:
                raise SnapshotNotFoundError(f"Snapshot {snapshot_name} not found in repository {repository_name}")
            raise SnapshotCreationError(f"Failed to get snapshot status: {str(e)}")
        except Exception as e:
            raise SnapshotCreationError(f"Failed to get snapshot status: {str(e)}")

    def delete_snapshot(
        self,
        snapshot_name: str,
        repository_name: str,
        source_cluster: Cluster
    ) -> None:
        """Delete a specific snapshot.
        
        Args:
            snapshot_name: Name of the snapshot to delete
            repository_name: Repository name
            source_cluster: Source cluster connection
            
        Raises:
            SnapshotNotFoundError: If snapshot doesn't exist
            SnapshotDeletionError: If deletion fails
        """
        try:
            path = f"/_snapshot/{repository_name}/{snapshot_name}"
            response = source_cluster.call_api(path, HttpMethod.DELETE)
            response.raise_for_status()
            
            logger.info(f"Deleted snapshot: {snapshot_name} from repository '{repository_name}'")
            
        except HTTPError as e:
            if e.response.status_code == 404:
                raise SnapshotNotFoundError(f"Snapshot {snapshot_name} not found in repository {repository_name}")
            raise SnapshotDeletionError(f"Failed to delete snapshot: {str(e)}")
        except Exception as e:
            raise SnapshotDeletionError(f"Failed to delete snapshot: {str(e)}")

    def delete_all_snapshots(
        self,
        repository_name: str,
        source_cluster: Cluster
    ) -> List[str]:
        """Delete all snapshots in a repository.
        
        Args:
            repository_name: Repository name
            source_cluster: Source cluster connection
            
        Returns:
            List of deleted snapshot names
            
        Raises:
            SnapshotDeletionError: If deletion fails
        """
        deleted_snapshots = []
        
        try:
            # List all snapshots
            snapshots_path = f"/_snapshot/{repository_name}/_all"
            response = source_cluster.call_api(snapshots_path, HttpMethod.GET)
            response.raise_for_status()
            
            snapshots = response.json().get("snapshots", [])
            logger.info(f"Found {len(snapshots)} snapshots in repository '{repository_name}'")
            
            # Delete each snapshot
            for snapshot in snapshots:
                snapshot_name = snapshot["snapshot"]
                try:
                    self.delete_snapshot(snapshot_name, repository_name, source_cluster)
                    deleted_snapshots.append(snapshot_name)
                except Exception as e:
                    logger.error(f"Failed to delete snapshot {snapshot_name}: {e}")
                    # Continue with other snapshots
            
            return deleted_snapshots
            
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"Repository '{repository_name}' not found")
                return []
            raise SnapshotDeletionError(f"Failed to list snapshots: {str(e)}")
        except Exception as e:
            raise SnapshotDeletionError(f"Failed to delete snapshots: {str(e)}")

    def delete_snapshot_repository(
        self,
        repository_name: str,
        source_cluster: Cluster
    ) -> None:
        """Delete a snapshot repository.
        
        Args:
            repository_name: Repository name to delete
            source_cluster: Source cluster connection
            
        Raises:
            SnapshotDeletionError: If deletion fails
        """
        try:
            delete_path = f"/_snapshot/{repository_name}"
            response = source_cluster.call_api(delete_path, method=HttpMethod.DELETE)
            response.raise_for_status()
            
            logger.info(f"Deleted repository: {repository_name}")
            
        except HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"Repository '{repository_name}' not found")
                return
            raise SnapshotDeletionError(f"Failed to delete repository: {str(e)}")
        except Exception as e:
            raise SnapshotDeletionError(f"Failed to delete repository: {str(e)}")

    def _build_s3_command_args(
        self,
        config: SnapshotConfig,
        s3_config: S3Config,
        source_cluster: ClusterEntity,
        wait: bool,
        max_snapshot_rate_mb_per_node: Optional[int],
        extra_args: Optional[List[str]]
    ) -> Dict:
        """Build command arguments for S3 snapshot creation."""
        command_args = self._build_universal_command_args(config, source_cluster)
        
        # Add S3-specific arguments
        command_args.update({
            "--s3-repo-uri": s3_config.repo_uri,
            "--s3-region": s3_config.region,
        })
        
        if s3_config.endpoint:
            command_args["--s3-endpoint"] = s3_config.endpoint
        
        if s3_config.role_arn:
            command_args["--s3-role-arn"] = s3_config.role_arn
        
        if not wait:
            command_args["--no-wait"] = FlagOnlyArgument
        
        if max_snapshot_rate_mb_per_node is not None:
            command_args["--max-snapshot-rate-mb-per-node"] = max_snapshot_rate_mb_per_node
        
        if extra_args:
            for arg in extra_args:
                command_args[arg] = FlagOnlyArgument
        
        return command_args

    def _build_filesystem_command_args(
        self,
        config: SnapshotConfig,
        repo_path: str,
        source_cluster: ClusterEntity,
        max_snapshot_rate_mb_per_node: Optional[int],
        extra_args: Optional[List[str]]
    ) -> Dict:
        """Build command arguments for filesystem snapshot creation."""
        command_args = self._build_universal_command_args(config, source_cluster)
        
        command_args["--file-system-repo-path"] = repo_path
        
        if max_snapshot_rate_mb_per_node is not None:
            command_args["--max-snapshot-rate-mb-per-node"] = max_snapshot_rate_mb_per_node
        
        if extra_args:
            for arg in extra_args:
                command_args[arg] = FlagOnlyArgument
        
        return command_args

    def _build_universal_command_args(
        self,
        config: SnapshotConfig,
        source_cluster: ClusterEntity
    ) -> Dict:
        """Build common command arguments for all snapshot types."""
        # Convert ClusterEntity to legacy Cluster for command building
        # This is temporary until we refactor the command execution layer
        from console_link.models.cluster import Cluster as LegacyCluster
        
        legacy_cluster = LegacyCluster(source_cluster.to_dict())
        
        command_args = {
            "--snapshot-name": config.snapshot_name,
            "--snapshot-repo-name": config.snapshot_repo_name,
            "--source-host": legacy_cluster.endpoint
        }
        
        # Handle authentication
        if legacy_cluster.auth_type:
            if legacy_cluster.auth_type.value == "basic":
                auth_details = legacy_cluster.get_basic_auth_details()
                command_args.update({
                    "--source-username": auth_details.username,
                    "--source-password": auth_details.password
                })
            elif legacy_cluster.auth_type.value == "sigv4":
                signing_name, region = legacy_cluster._get_sigv4_details(force_region=True)
                command_args.update({
                    "--source-aws-service-signing-name": signing_name,
                    "--source-aws-region": region
                })
        
        if source_cluster.allow_insecure:
            command_args["--source-insecure"] = None
        
        if config.otel_endpoint:
            command_args["--otel-collector-endpoint"] = config.otel_endpoint
        
        return command_args
