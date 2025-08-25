"""Domain exceptions for metrics operations."""

from console_link.domain.exceptions.common_errors import MigrationAssistantError


class MetricsError(MigrationAssistantError):
    """Base exception for metrics-related errors."""
    pass


class MetricsRetrievalError(MetricsError):
    """Exception raised when retrieving metrics fails."""
    pass


class MetricsParsingError(MetricsError):
    """Exception raised when parsing metrics data fails."""
    pass
