"""CLI error handlers."""
import logging
import click
from typing import Optional

from console_link.domain.exceptions.snapshot_errors import (
    SnapshotError,
    SnapshotCreationError,
    SnapshotNotFoundError,
    SnapshotValidationError
)
from console_link.domain.exceptions.cluster_errors import (
    ClusterError,
    ClusterConnectionError,
    ClusterAuthenticationError,
    ClusterOperationError
)
from console_link.domain.exceptions.backfill_errors import (
    BackfillError,
    BackfillValidationError,
    BackfillCreationError,
    BackfillStopError,
    BackfillNotFoundError
)
from console_link.domain.exceptions.common_errors import (
    MigrationAssistantError,
    ValidationError,
    ConfigurationError,
    InfrastructureError,
    OperationError
)

logger = logging.getLogger(__name__)


class CLIErrorHandler:
    """Handles errors for CLI commands."""
    
    def __init__(self, json_output: bool = False):
        """Initialize error handler.
        
        Args:
            json_output: Whether to format errors as JSON
        """
        self.json_output = json_output
    
    def handle_error(self, error: Exception, exit_code: Optional[int] = None) -> None:
        """Handle an error by logging and formatting it appropriately.
        
        Args:
            error: The error to handle
            exit_code: Optional exit code to use (default based on error type)
        """
        # Log the error with appropriate level
        if isinstance(error, ValidationError):
            logger.warning(f"Validation error: {error}")
        elif isinstance(error, MigrationAssistantError):
            logger.error(f"Domain error: {error}")
        else:
            logger.exception(f"Unexpected error: {error}")
        
        # Format error message
        message = self._format_error_message(error)
        
        # Determine exit code
        if exit_code is None:
            exit_code = self._get_exit_code(error)
        
        # Raise ClickException to properly exit
        raise click.ClickException(message) from error
    
    def _format_error_message(self, error: Exception) -> str:
        """Format error message based on error type.
        
        Args:
            error: The error to format
            
        Returns:
            Formatted error message
        """
        if self.json_output:
            import json
            return json.dumps({
                "error": True,
                "type": type(error).__name__,
                "message": str(error),
                "details": self._get_error_details(error)
            }, indent=2)
        
        # Human-readable format
        if isinstance(error, SnapshotValidationError):
            return f"❌ Invalid snapshot configuration: {error}"
        elif isinstance(error, SnapshotCreationError):
            return f"❌ Failed to create snapshot: {error}"
        elif isinstance(error, SnapshotNotFoundError):
            return f"❌ Snapshot not found: {error}"
        elif isinstance(error, SnapshotError):
            return f"❌ Snapshot error: {error}"
        
        elif isinstance(error, ClusterConnectionError):
            return f"❌ Failed to connect to cluster: {error}"
        elif isinstance(error, ClusterAuthenticationError):
            return f"❌ Authentication failed: {error}"
        elif isinstance(error, ClusterOperationError):
            return f"❌ Cluster operation failed: {error}"
        elif isinstance(error, ClusterError):
            return f"❌ Cluster error: {error}"
        
        elif isinstance(error, BackfillValidationError):
            return f"❌ Invalid backfill configuration: {error}"
        elif isinstance(error, (BackfillCreationError, BackfillStopError)):
            return f"❌ Backfill operation failed: {error}"
        elif isinstance(error, BackfillNotFoundError):
            return f"❌ Backfill not found: {error}"
        elif isinstance(error, BackfillError):
            return f"❌ Backfill error: {error}"
        
        elif isinstance(error, ValidationError):
            return f"❌ Validation error: {error}"
        elif isinstance(error, ConfigurationError):
            return f"❌ Configuration error: {error}"
        elif isinstance(error, InfrastructureError):
            return f"❌ Infrastructure error: {error}"
        elif isinstance(error, MigrationAssistantError):
            return f"❌ Domain error: {error}"
        
        # Generic error
        return f"❌ Error: {error}"
    
    def _get_error_details(self, error: Exception) -> dict:
        """Get additional error details for JSON output.
        
        Args:
            error: The error to get details for
            
        Returns:
            Dictionary of error details
        """
        details = {}
        
        # Add any error-specific details
        if hasattr(error, "__dict__"):
            for key, value in error.__dict__.items():
                if not key.startswith("_") and key != "args":
                    details[key] = str(value)
        
        return details
    
    def _get_exit_code(self, error: Exception) -> int:
        """Get appropriate exit code for error type.
        
        Args:
            error: The error to get exit code for
            
        Returns:
            Exit code
        """
        if isinstance(error, ValidationError):
            return 2  # Invalid input
        elif isinstance(error, (SnapshotNotFoundError, BackfillNotFoundError)):
            return 3  # Not found
        elif isinstance(error, (ClusterConnectionError, ClusterAuthenticationError)):
            return 4  # Connection/auth error
        elif isinstance(error, ConfigurationError):
            return 5  # Configuration error
        elif isinstance(error, InfrastructureError):
            return 6  # Infrastructure error
        elif isinstance(error, MigrationAssistantError):
            return 10  # General domain error
        else:
            return 1  # General error


def handle_snapshot_error(error: SnapshotError, json_output: bool = False) -> None:
    """Convenience function to handle snapshot errors.
    
    Args:
        error: The snapshot error
        json_output: Whether to format as JSON
    """
    handler = CLIErrorHandler(json_output)
    handler.handle_error(error)


def handle_cluster_error(error: ClusterError, json_output: bool = False) -> None:
    """Convenience function to handle cluster errors.
    
    Args:
        error: The cluster error
        json_output: Whether to format as JSON
    """
    handler = CLIErrorHandler(json_output)
    handler.handle_error(error)


def handle_backfill_error(error: BackfillError, json_output: bool = False) -> None:
    """Convenience function to handle backfill errors.
    
    Args:
        error: The backfill error
        json_output: Whether to format as JSON
    """
    handler = CLIErrorHandler(json_output)
    handler.handle_error(error)
