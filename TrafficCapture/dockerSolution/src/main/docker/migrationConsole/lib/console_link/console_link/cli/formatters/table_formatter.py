"""Table formatter for CLI output."""
import json
from typing import Any, Dict, List, Optional
from tabulate import tabulate

from console_link.cli.formatters.base_formatter import BaseFormatter


class TableFormatter(BaseFormatter):
    """Formatter that outputs data in table format."""
    
    def __init__(self, json_output: bool = False, table_format: str = "grid"):
        """Initialize table formatter.
        
        Args:
            json_output: Whether to format output as JSON
            table_format: Tabulate format (grid, simple, pretty, etc.)
        """
        super().__init__(json_output)
        self.table_format = table_format
    
    def format_entity(self, entity: Any) -> str:
        """Format a single entity for display.
        
        Args:
            entity: The entity to format
            
        Returns:
            Formatted string representation
        """
        if self.json_output:
            return json.dumps(self._entity_to_dict(entity), indent=2)
        
        # Convert entity to dict for table display
        entity_dict = self._entity_to_dict(entity)
        
        # Create key-value pairs for table
        rows = [[key, value] for key, value in entity_dict.items()]
        
        return tabulate(rows, headers=["Field", "Value"], tablefmt=self.table_format)
    
    def format_list(self, entities: List[Any], headers: Optional[List[str]] = None) -> str:
        """Format a list of entities for display.
        
        Args:
            entities: List of entities to format
            headers: Optional column headers
            
        Returns:
            Formatted string representation
        """
        if not entities:
            return self.format_info("No items found")
        
        if self.json_output:
            return json.dumps([self._entity_to_dict(e) for e in entities], indent=2)
        
        # Convert entities to list of dicts
        entity_dicts = [self._entity_to_dict(e) for e in entities]
        
        # If no headers provided, use keys from first entity
        if headers is None and entity_dicts:
            headers = list(entity_dicts[0].keys())
        
        # Extract values in same order as headers
        rows = []
        for entity_dict in entity_dicts:
            row = [entity_dict.get(h, "") for h in headers] if headers else list(entity_dict.values())
            rows.append(row)
        
        return tabulate(rows, headers=headers, tablefmt=self.table_format)
    
    def format_error(self, error: Exception) -> str:
        """Format an error for display.
        
        Args:
            error: The error to format
            
        Returns:
            Formatted error message
        """
        if self.json_output:
            return json.dumps({
                "error": True,
                "type": type(error).__name__,
                "message": str(error)
            }, indent=2)
        
        return f"❌ Error ({type(error).__name__}): {str(error)}"
    
    def format_status(self, status: Dict[str, Any]) -> str:
        """Format a status dictionary for display.
        
        Args:
            status: Status information
            
        Returns:
            Formatted status representation
        """
        if self.json_output:
            return json.dumps(status, indent=2)
        
        # Create key-value pairs for table
        rows = []
        for key, value in status.items():
            if isinstance(value, dict):
                # Nested dict - flatten one level
                for sub_key, sub_value in value.items():
                    rows.append([f"{key}.{sub_key}", str(sub_value)])
            elif isinstance(value, list):
                rows.append([key, ", ".join(str(v) for v in value)])
            else:
                rows.append([key, str(value)])
        
        return tabulate(rows, headers=["Status Field", "Value"], tablefmt=self.table_format)
    
    def _entity_to_dict(self, entity: Any) -> Dict[str, Any]:
        """Convert an entity to a dictionary.
        
        Args:
            entity: Entity to convert
            
        Returns:
            Dictionary representation
        """
        if hasattr(entity, "__dict__"):
            return {k: v for k, v in entity.__dict__.items() if not k.startswith("_")}
        elif hasattr(entity, "dict"):
            # Pydantic models
            return entity.dict()
        elif hasattr(entity, "to_dict"):
            return entity.to_dict()
        elif isinstance(entity, dict):
            return entity
        else:
            # Fallback for dataclasses
            from dataclasses import asdict, is_dataclass
            if is_dataclass(entity):
                return asdict(entity)
            return {"value": str(entity)}
