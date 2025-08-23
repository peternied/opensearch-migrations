"""
Domain-specific exceptions for snapshot operations.
"""

from console_link.domain.exceptions.common_errors import MigrationAssistantError, ValidationError, NotFoundError


class SnapshotError(MigrationAssistantError):
    """Base exception for all snapshot-related errors."""
    pass


class SnapshotValidationError(SnapshotError, ValidationError):
    """Raised when snapshot configuration or parameters are invalid."""
    pass


class SnapshotCreationError(SnapshotError):
    """Raised when snapshot creation fails."""
    pass


class SnapshotNotFoundError(SnapshotError, NotFoundError):
    """Raised when a snapshot cannot be found."""
    pass


class SnapshotNotStartedError(SnapshotError):
    """Raised when attempting to get status of a snapshot that hasn't started."""
    pass


class SnapshotStatusUnavailableError(SnapshotError):
    """Raised when snapshot status information is not available."""
    pass


class SnapshotDeletionError(SnapshotError):
    """Raised when snapshot deletion fails."""
    pass


class SnapshotRepositoryError(SnapshotError):
    """Base exception for snapshot repository errors."""
    pass


class SnapshotRepositoryNotFoundError(SnapshotRepositoryError, NotFoundError):
    """Raised when a snapshot repository cannot be found."""
    pass


class SnapshotRepositoryDeletionError(SnapshotRepositoryError):
    """Raised when snapshot repository deletion fails."""
    pass


class SourceClusterNotDefinedError(SnapshotError):
    """Raised when attempting snapshot operations without a source cluster."""
    pass
