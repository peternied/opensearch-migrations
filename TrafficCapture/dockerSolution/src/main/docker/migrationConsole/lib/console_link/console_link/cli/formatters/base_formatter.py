"""Base formatter for CLI output."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseFormatter(ABC):
    """Base class for all CLI formatters."""
    
    def __init__(self, json_output: bool = False):
        """Initialize formatter.
        
        Args:
            json_output: Whether to format output as JSON
        """
        self.json_output = json_output
    
    @abstractmethod
    def format_entity(self, entity: Any) -> str:
        """Format a single entity for display.
        
        Args:
            entity: The entity to format
            
        Returns:
            Formatted string representation
        """
        pass
    
    @abstractmethod
    def format_list(self, entities: List[Any], headers: Optional[List[str]] = None) -> str:
        """Format a list of entities for display.
        
        Args:
            entities: List of entities to format
            headers: Optional column headers
            
        Returns:
            Formatted string representation
        """
        pass
    
    @abstractmethod
    def format_error(self, error: Exception) -> str:
        """Format an error for display.
        
        Args:
            error: The error to format
            
        Returns:
            Formatted error message
        """
        pass
    
    @abstractmethod
    def format_status(self, status: Dict[str, Any]) -> str:
        """Format a status dictionary for display.
        
        Args:
            status: Status information
            
        Returns:
            Formatted status representation
        """
        pass
    
    def format_success(self, message: str) -> str:
        """Format a success message.
        
        Args:
            message: Success message
            
        Returns:
            Formatted success message
        """
        if self.json_output:
            import json
            return json.dumps({"success": True, "message": message})
        return f"✓ {message}"
    
    def format_warning(self, message: str) -> str:
        """Format a warning message.
        
        Args:
            message: Warning message
            
        Returns:
            Formatted warning message
        """
        if self.json_output:
            import json
            return json.dumps({"warning": True, "message": message})
        return f"⚠ {message}"
    
    def format_info(self, message: str) -> str:
        """Format an info message.
        
        Args:
            message: Info message
            
        Returns:
            Formatted info message
        """
        if self.json_output:
            import json
            return json.dumps({"info": True, "message": message})
        return f"ℹ {message}"
