"""Replay service for handling traffic replay operations.

This service handles replay start, stop, scale and status operations,
raising exceptions on errors instead of returning CommandResult objects.
"""

import logging
from typing import Tuple
from console_link.models.replayer_base import Replayer, ReplayStatus
from console_link.domain.exceptions.replay_errors import (
    ReplayStartError,
    ReplayStopError,
    ReplayScaleError,
    ReplayStatusError
)

logger = logging.getLogger(__name__)


class ReplayService:
    """Service for handling replay operations."""
    
    def __init__(self, replayer: Replayer):
        """Initialize the replay service.
        
        Args:
            replayer: The replayer model instance
        """
        self.replayer = replayer
    
    def start(self) -> str:
        """Start the replay process.
        
        Returns:
            Success message
            
        Raises:
            ReplayStartError: If starting replay fails
        """
        try:
            result = self.replayer.start()
            if not result.success:
                raise ReplayStartError(f"Failed to start replay: {result.value}")
            return str(result.value)
        except Exception as e:
            logger.error(f"Failed to start replay: {e}")
            raise ReplayStartError(f"Replay start failed: {str(e)}")
    
    def stop(self) -> str:
        """Stop the replay process.
        
        Returns:
            Success message
            
        Raises:
            ReplayStopError: If stopping replay fails
        """
        try:
            result = self.replayer.stop()
            if not result.success:
                raise ReplayStopError(f"Failed to stop replay: {result.value}")
            return str(result.value)
        except Exception as e:
            logger.error(f"Failed to stop replay: {e}")
            raise ReplayStopError(f"Replay stop failed: {str(e)}")
    
    def scale(self, units: int) -> str:
        """Scale the replay process.
        
        Args:
            units: Number of units to scale to
            
        Returns:
            Success message
            
        Raises:
            ReplayScaleError: If scaling replay fails
        """
        try:
            if units < 0:
                raise ReplayScaleError("Units must be non-negative")
                
            result = self.replayer.scale(units)
            if not result.success:
                raise ReplayScaleError(f"Failed to scale replay: {result.value}")
            return str(result.value)
        except Exception as e:
            logger.error(f"Failed to scale replay: {e}")
            raise ReplayScaleError(f"Replay scale failed: {str(e)}")
    
    def get_status(self) -> Tuple[ReplayStatus, str]:
        """Get the status of the replay process.
        
        Returns:
            Tuple of (status, status_message)
            
        Raises:
            ReplayStatusError: If getting status fails
        """
        try:
            result = self.replayer.get_status()
            if not result.success:
                raise ReplayStatusError(f"Failed to get replay status: {result.value}")
            
            # The value should be a tuple of (ReplayStatus, str)
            if isinstance(result.value, tuple) and len(result.value) == 2:
                return result.value
            else:
                # Handle unexpected format
                return ReplayStatus.FAILED, str(result.value)
        except Exception as e:
            logger.error(f"Failed to get replay status: {e}")
            raise ReplayStatusError(f"Failed to get replay status: {str(e)}")
