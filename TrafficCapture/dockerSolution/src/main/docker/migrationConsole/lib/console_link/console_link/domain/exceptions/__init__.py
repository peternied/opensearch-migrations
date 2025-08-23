"""Domain exceptions for the migration assistant."""

from .backfill_errors import *
from .cluster_errors import *
from .common_errors import *
from .snapshot_errors import *

__all__ = [
    # Common errors
    "MigrationAssistantError",
    "ValidationError",
    "NotFoundError",
    "OperationError",
    "ConfigurationError",
    "AuthenticationError",
    "AuthorizationError",
    "ExternalServiceError",
    "TimeoutError",
    "ConcurrencyError",
    "DataIntegrityError",
    # Snapshot errors
    "SnapshotError",
    "SnapshotValidationError",
    "SnapshotCreationError",
    "SnapshotNotFoundError",
    "SnapshotNotStartedError",
    "SnapshotStatusUnavailableError",
    "SnapshotDeletionError",
    "SnapshotRepositoryError",
    "SnapshotRepositoryNotFoundError",
    "SnapshotRepositoryDeletionError",
    "SourceClusterNotDefinedError",
    # Cluster errors
    "ClusterError",
    "ClusterValidationError",
    "ClusterConnectionError",
    "ClusterNotFoundError",
    "ClusterAuthenticationError",
    "ClusterAuthorizationError",
    "ClusterOperationError",
    "NoSourceClusterDefinedError",
    "NoTargetClusterDefinedError",
    "ClusterHealthCheckError",
    "ClusterAPIError",
    # Backfill errors
    "BackfillError",
    "BackfillValidationError",
    "BackfillNotFoundError",
    "BackfillAlreadyRunningError",
    "BackfillNotRunningError",
    "BackfillCreationError",
    "BackfillStopError",
    "BackfillStatusError",
    "BackfillScaleError",
    "BackfillWorkItemError",
    "BackfillWorkItemNotFoundError",
    "BackfillWorkItemUpdateError",
    "BackfillWorkCoordinationError",
]
