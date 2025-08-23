"""Data conversion utilities for console_link.

This module provides functions for converting between different data formats
and representations used throughout the application.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict, is_dataclass
from enum import Enum

from console_link.shared.constants import (
    ISO_DATETIME_FORMAT,
    ISO_DATETIME_FORMAT_WITH_TZ,
    BYTES_PER_KB,
    BYTES_PER_MB,
    BYTES_PER_GB
)


def to_dict(obj: Any) -> Dict[str, Any]:
    """Convert an object to a dictionary.
    
    Handles dataclasses, Pydantic models, and objects with __dict__.
    
    Args:
        obj: The object to convert
        
    Returns:
        Dictionary representation of the object
    """
    if is_dataclass(obj):
        return asdict(obj)
    elif hasattr(obj, 'dict') and callable(obj.dict):
        # Pydantic model
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    elif isinstance(obj, dict):
        return obj
    else:
        raise ValueError(f"Cannot convert {type(obj)} to dict")


def to_json(obj: Any, indent: Optional[int] = None) -> str:
    """Convert an object to JSON string.
    
    Args:
        obj: The object to convert
        indent: Number of spaces for indentation (None for compact)
        
    Returns:
        JSON string representation
    """
    return json.dumps(to_dict(obj), default=_json_default, indent=indent)


def _json_default(obj: Any) -> Any:
    """Default JSON serializer for non-standard types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def from_json(json_str: str) -> Dict[str, Any]:
    """Parse a JSON string to a dictionary.
    
    Args:
        json_str: The JSON string to parse
        
    Returns:
        Parsed dictionary
        
    Raises:
        ValueError: If the JSON is invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def bytes_to_human_readable(size_bytes: Union[int, float]) -> str:
    """Convert bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    if size_bytes < BYTES_PER_KB:
        return f"{size_bytes} B"
    elif size_bytes < BYTES_PER_MB:
        return f"{size_bytes / BYTES_PER_KB:.2f} KB"
    elif size_bytes < BYTES_PER_GB:
        return f"{size_bytes / BYTES_PER_MB:.2f} MB"
    else:
        return f"{size_bytes / BYTES_PER_GB:.2f} GB"


def human_readable_to_bytes(size_str: str) -> int:
    """Convert human-readable size to bytes.
    
    Args:
        size_str: Size string (e.g., "1.5 MB", "2GB", "512KB")
        
    Returns:
        Size in bytes
        
    Raises:
        ValueError: If the format is invalid
    """
    size_str = size_str.strip().upper()
    
    # Extract number and unit
    import re
    match = re.match(r'^([\d.]+)\s*([KMGT]?B)?$', size_str)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")
    
    number = float(match.group(1))
    unit = match.group(2) or 'B'
    
    multipliers = {
        'B': 1,
        'KB': BYTES_PER_KB,
        'MB': BYTES_PER_MB,
        'GB': BYTES_PER_GB,
        'TB': BYTES_PER_GB * 1024
    }
    
    if unit not in multipliers:
        raise ValueError(f"Unknown unit: {unit}")
    
    return int(number * multipliers[unit])


def seconds_to_human_readable(seconds: Union[int, float]) -> str:
    """Convert seconds to human-readable duration.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration (e.g., "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def timestamp_to_datetime(timestamp: Union[int, float, str]) -> datetime:
    """Convert various timestamp formats to datetime.
    
    Args:
        timestamp: Unix timestamp (seconds or milliseconds) or ISO string
        
    Returns:
        datetime object
    """
    if isinstance(timestamp, str):
        # Try parsing as ISO format
        for fmt in [ISO_DATETIME_FORMAT_WITH_TZ, ISO_DATETIME_FORMAT]:
            try:
                return datetime.strptime(timestamp, fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse timestamp string: {timestamp}")
    
    # Numeric timestamp
    timestamp_float = float(timestamp)
    
    # Detect if it's in milliseconds (rough heuristic)
    if timestamp_float > 1e10:
        return datetime.fromtimestamp(timestamp_float / 1000)
    else:
        return datetime.fromtimestamp(timestamp_float)


def datetime_to_iso(dt: datetime, with_timezone: bool = True) -> str:
    """Convert datetime to ISO format string.
    
    Args:
        dt: datetime object
        with_timezone: Whether to include timezone (Z suffix)
        
    Returns:
        ISO format string
    """
    if with_timezone:
        return dt.strftime(ISO_DATETIME_FORMAT_WITH_TZ)
    else:
        return dt.strftime(ISO_DATETIME_FORMAT)


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to camelCase.
    
    Args:
        snake_str: String in snake_case
        
    Returns:
        String in camelCase
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case.
    
    Args:
        camel_str: String in camelCase
        
    Returns:
        String in snake_case
    """
    import re
    # Insert underscore before uppercase letters
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def flatten_dict(
    nested_dict: Dict[str, Any],
    parent_key: str = '',
    separator: str = '.'
) -> Dict[str, Any]:
    """Flatten a nested dictionary.
    
    Args:
        nested_dict: Dictionary to flatten
        parent_key: Prefix for keys (used in recursion)
        separator: Separator between nested keys
        
    Returns:
        Flattened dictionary
    """
    items: List[tuple] = []
    for k, v in nested_dict.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(
    flat_dict: Dict[str, Any],
    separator: str = '.'
) -> Dict[str, Any]:
    """Unflatten a dictionary.
    
    Args:
        flat_dict: Flattened dictionary
        separator: Separator used in flattened keys
        
    Returns:
        Nested dictionary
    """
    result: Dict[str, Any] = {}
    for key, value in flat_dict.items():
        parts = key.split(separator)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def safe_get(
    data: Dict[str, Any],
    key_path: str,
    default: Any = None,
    separator: str = '.'
) -> Any:
    """Safely get a value from a nested dictionary.
    
    Args:
        data: The dictionary to search
        key_path: Dot-separated path to the value
        default: Default value if key not found
        separator: Key path separator
        
    Returns:
        The value if found, otherwise default
    """
    keys = key_path.split(separator)
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Values from dict2 override values in dict1.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result
