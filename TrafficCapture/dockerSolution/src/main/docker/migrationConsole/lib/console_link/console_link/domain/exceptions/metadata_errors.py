"""Domain exceptions for metadata operations."""

from console_link.domain.exceptions.common_errors import MigrationAssistantError


class MetadataError(MigrationAssistantError):
    """Base exception for metadata-related errors."""
    pass


class MetadataEvaluationError(MetadataError):
    """Exception raised when metadata evaluation fails."""
    pass


class MetadataMigrationError(MetadataError):
    """Exception raised when metadata migration fails."""
    pass


class MetadataParsingError(MetadataError):
    """Exception raised when parsing metadata output fails."""
    pass
