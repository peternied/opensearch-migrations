"""
Domain-specific exceptions for backfill operations.
"""

from console_link.domain.exceptions.common_errors import MigrationAssistantError, ValidationError, NotFoundError


class BackfillError(MigrationAssistantError):
    """Base exception for all backfill-related errors."""
    pass


class BackfillValidationError(BackfillError, ValidationError):
    """Raised when backfill configuration or parameters are invalid."""
    pass


class BackfillNotFoundError(BackfillError, NotFoundError):
    """Raised when a backfill cannot be found."""
    pass


class BackfillAlreadyRunningError(BackfillError):
    """Raised when attempting to start a backfill that is already running."""
    pass


class BackfillNotRunningError(BackfillError):
    """Raised when attempting to stop a backfill that is not running."""
    pass


class BackfillCreationError(BackfillError):
    """Raised when backfill creation fails."""
    pass


class BackfillStopError(BackfillError):
    """Raised when stopping a backfill fails."""
    pass


class BackfillStatusError(BackfillError):
    """Raised when getting backfill status fails."""
    pass


class BackfillScaleError(BackfillError):
    """Raised when scaling a backfill fails."""
    pass


class BackfillWorkItemError(BackfillError):
    """Base exception for backfill work item errors."""
    pass


class BackfillWorkItemNotFoundError(BackfillWorkItemError, NotFoundError):
    """Raised when a backfill work item cannot be found."""
    pass


class BackfillWorkItemUpdateError(BackfillWorkItemError):
    """Raised when updating a backfill work item fails."""
    pass


class BackfillWorkCoordinationError(BackfillError):
    """Raised when work coordination operations fail."""
    pass
