"""Domain exceptions for replay operations."""

from console_link.domain.exceptions.common_errors import MigrationAssistantError


class ReplayError(MigrationAssistantError):
    """Base exception for replay-related errors."""
    pass


class ReplayStartError(ReplayError):
    """Exception raised when starting replay fails."""
    pass


class ReplayStopError(ReplayError):
    """Exception raised when stopping replay fails."""
    pass


class ReplayScaleError(ReplayError):
    """Exception raised when scaling replay fails."""
    pass


class ReplayStatusError(ReplayError):
    """Exception raised when getting replay status fails."""
    pass
