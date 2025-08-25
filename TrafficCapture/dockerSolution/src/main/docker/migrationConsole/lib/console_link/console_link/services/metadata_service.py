"""Metadata service for handling metadata operations.

This service handles metadata evaluation and migration operations,
raising exceptions on errors instead of returning CommandResult objects.
"""

import logging
from typing import Any, Dict, Optional
from console_link.models.metadata import Metadata
from console_link.domain.exceptions.metadata_errors import (
    MetadataEvaluationError,
    MetadataMigrationError,
    MetadataParsingError
)

logger = logging.getLogger(__name__)


class MetadataService:
    """Service for handling metadata operations."""
    
    def __init__(self, metadata: Metadata):
        """Initialize the metadata service.
        
        Args:
            metadata: The metadata model instance
        """
        self.metadata = metadata
    
    def evaluate(self, extra_args: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate metadata migration.
        
        Args:
            extra_args: Additional arguments for the evaluation
            
        Returns:
            Evaluation results as a dictionary
            
        Raises:
            MetadataEvaluationError: If evaluation fails
        """
        try:
            result = self.metadata.evaluate(extra_args)
            if not result.success:
                raise MetadataEvaluationError(f"Evaluation failed: {result.value}")
            
            # Parse the result
            return self._parse_result(str(result.value))
        except Exception as e:
            logger.error(f"Failed to evaluate metadata: {e}")
            raise MetadataEvaluationError(f"Metadata evaluation failed: {str(e)}")
    
    def migrate(self, extra_args: Optional[str] = None) -> Dict[str, Any]:
        """Migrate metadata.
        
        Args:
            extra_args: Additional arguments for the migration
            
        Returns:
            Migration results as a dictionary
            
        Raises:
            MetadataMigrationError: If migration fails
        """
        try:
            result = self.metadata.migrate(extra_args)
            if not result.success:
                raise MetadataMigrationError(f"Migration failed: {result.value}")
            
            # Parse the result
            return self._parse_result(str(result.value))
        except Exception as e:
            logger.error(f"Failed to migrate metadata: {e}")
            raise MetadataMigrationError(f"Metadata migration failed: {str(e)}")
    
    def _parse_result(self, output: str) -> Dict[str, Any]:
        """Parse metadata command output.
        
        Args:
            output: The command output to parse
            
        Returns:
            Parsed results as a dictionary
            
        Raises:
            MetadataParsingError: If parsing fails
        """
        try:
            # For now, return a simple dict with the output
            # In the future, this should parse structured output
            return {
                "output": output,
                "success": True
            }
        except Exception as e:
            logger.error(f"Failed to parse metadata result: {e}")
            raise MetadataParsingError(f"Failed to parse metadata result: {str(e)}")
