"""Shared validation functions for console_link.

This module provides common validation functions that can be used
across different components of the application.
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from console_link.domain.exceptions.common_errors import ValidationError


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present in the data.
    
    Args:
        data: Dictionary containing the data to validate
        required_fields: List of field names that must be present
        
    Raises:
        ValidationError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")


def validate_not_empty(value: Any, field_name: str) -> None:
    """Validate that a value is not empty.
    
    Args:
        value: The value to check
        field_name: Name of the field (for error messages)
        
    Raises:
        ValidationError: If the value is empty
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValidationError(f"{field_name} cannot be empty")


def validate_url(url: str, field_name: str = "URL", require_scheme: bool = True) -> None:
    """Validate that a string is a valid URL.
    
    Args:
        url: The URL string to validate
        field_name: Name of the field (for error messages)
        require_scheme: Whether to require a scheme (http/https)
        
    Raises:
        ValidationError: If the URL is invalid
    """
    validate_not_empty(url, field_name)
    
    try:
        result = urlparse(url)
        if require_scheme and not result.scheme:
            raise ValidationError(f"{field_name} must include a scheme (http:// or https://)")
        if not result.netloc:
            raise ValidationError(f"{field_name} must include a host")
    except Exception as e:
        raise ValidationError(f"Invalid {field_name}: {str(e)}")


def validate_endpoint(endpoint: str) -> None:
    """Validate an Elasticsearch/OpenSearch endpoint.
    
    Args:
        endpoint: The endpoint URL to validate
        
    Raises:
        ValidationError: If the endpoint is invalid
    """
    validate_url(endpoint, "Endpoint")
    
    # Additional endpoint-specific validation
    parsed = urlparse(endpoint)
    if parsed.scheme not in ['http', 'https']:
        raise ValidationError("Endpoint must use http or https scheme")


def validate_aws_region(region: str) -> None:
    """Validate an AWS region name.
    
    Args:
        region: The AWS region to validate
        
    Raises:
        ValidationError: If the region is invalid
    """
    validate_not_empty(region, "AWS region")
    
    # Basic AWS region pattern
    region_pattern = r'^[a-z]{2}-[a-z]+-\d{1}$'
    if not re.match(region_pattern, region):
        raise ValidationError(f"Invalid AWS region format: {region}")


def validate_s3_uri(uri: str) -> None:
    """Validate an S3 URI.
    
    Args:
        uri: The S3 URI to validate
        
    Raises:
        ValidationError: If the URI is invalid
    """
    validate_not_empty(uri, "S3 URI")
    
    if not uri.startswith("s3://"):
        raise ValidationError("S3 URI must start with 's3://'")
    
    # Extract bucket and key
    parts = uri[5:].split('/', 1)
    if not parts[0]:
        raise ValidationError("S3 URI must include a bucket name")
    
    # Validate bucket name (simplified rules)
    bucket_pattern = r'^[a-z0-9][a-z0-9\-\.]*[a-z0-9]$'
    if not re.match(bucket_pattern, parts[0]):
        raise ValidationError(f"Invalid S3 bucket name: {parts[0]}")


def validate_port(port: Union[int, str], field_name: str = "Port") -> int:
    """Validate a port number.
    
    Args:
        port: The port number to validate (int or string)
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated port as an integer
        
    Raises:
        ValidationError: If the port is invalid
    """
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValidationError(f"{field_name} must be between 1 and 65535")
        return port_int
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a number")


def validate_percentage(value: Union[int, float], field_name: str = "Percentage") -> float:
    """Validate a percentage value.
    
    Args:
        value: The percentage value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated percentage as a float
        
    Raises:
        ValidationError: If the percentage is invalid
    """
    try:
        percentage = float(value)
        if percentage < 0 or percentage > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100")
        return percentage
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a number")


def validate_positive_integer(value: Union[int, str], field_name: str) -> int:
    """Validate a positive integer.
    
    Args:
        value: The value to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        The validated integer
        
    Raises:
        ValidationError: If the value is not a positive integer
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValidationError(f"{field_name} must be a positive integer")
        return int_value
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a positive integer")


def validate_file_path(path: str, must_exist: bool = False) -> None:
    """Validate a file path.
    
    Args:
        path: The file path to validate
        must_exist: Whether the file must already exist
        
    Raises:
        ValidationError: If the path is invalid
    """
    validate_not_empty(path, "File path")
    
    if must_exist:
        from pathlib import Path
        if not Path(path).exists():
            raise ValidationError(f"File not found: {path}")


def validate_choice(value: str, choices: List[str], field_name: str) -> None:
    """Validate that a value is one of the allowed choices.
    
    Args:
        value: The value to validate
        choices: List of allowed values
        field_name: Name of the field (for error messages)
        
    Raises:
        ValidationError: If the value is not in choices
    """
    if value not in choices:
        raise ValidationError(
            f"Invalid {field_name}: '{value}'. Must be one of: {', '.join(choices)}"
        )


def validate_snapshot_name(name: str) -> None:
    """Validate a snapshot name.
    
    Args:
        name: The snapshot name to validate
        
    Raises:
        ValidationError: If the name is invalid
    """
    validate_not_empty(name, "Snapshot name")
    
    # Elasticsearch/OpenSearch snapshot naming rules
    if not re.match(r'^[a-z0-9_\-]+$', name.lower()):
        raise ValidationError(
            "Snapshot name must contain only lowercase letters, numbers, "
            "hyphens, and underscores"
        )
    
    if name.startswith('-') or name.startswith('_'):
        raise ValidationError("Snapshot name cannot start with '-' or '_'")


def validate_index_name(name: str) -> None:
    """Validate an index name.
    
    Args:
        name: The index name to validate
        
    Raises:
        ValidationError: If the name is invalid
    """
    validate_not_empty(name, "Index name")
    
    # Elasticsearch/OpenSearch index naming rules
    if name != name.lower():
        raise ValidationError("Index name must be lowercase")
    
    invalid_chars = ['\\', '/', '*', '?', '"', '<', '>', '|', ' ', ',', '#']
    for char in invalid_chars:
        if char in name:
            raise ValidationError(f"Index name cannot contain '{char}'")
    
    if name.startswith('-') or name.startswith('_') or name.startswith('+'):
        raise ValidationError("Index name cannot start with '-', '_', or '+'")
    
    if name == '.' or name == '..':
        raise ValidationError("Index name cannot be '.' or '..'")
