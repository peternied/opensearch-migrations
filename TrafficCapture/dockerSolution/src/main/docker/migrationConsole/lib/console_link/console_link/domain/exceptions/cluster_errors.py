"""
Domain-specific exceptions for cluster operations.
"""

from console_link.domain.exceptions.common_errors import MigrationAssistantError, ValidationError, NotFoundError


class ClusterError(MigrationAssistantError):
    """Base exception for all cluster-related errors."""
    pass


class ClusterValidationError(ClusterError, ValidationError):
    """Raised when cluster configuration or parameters are invalid."""
    pass


class ClusterConnectionError(ClusterError):
    """Raised when unable to connect to a cluster."""
    pass


class ClusterNotFoundError(ClusterError, NotFoundError):
    """Raised when a cluster cannot be found."""
    pass


class ClusterAuthenticationError(ClusterError):
    """Raised when cluster authentication fails."""
    pass


class ClusterAuthorizationError(ClusterError):
    """Raised when cluster authorization fails."""
    pass


class ClusterOperationError(ClusterError):
    """Raised when a cluster operation fails."""
    pass


class NoSourceClusterDefinedError(ClusterError):
    """Raised when attempting operations without a source cluster."""
    pass


class NoTargetClusterDefinedError(ClusterError):
    """Raised when attempting operations without a target cluster."""
    pass


class ClusterHealthCheckError(ClusterError):
    """Raised when cluster health check fails."""
    pass


class ClusterAPIError(ClusterError):
    """Raised when a cluster API call fails."""
    pass
