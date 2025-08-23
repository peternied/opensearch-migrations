"""Value objects for S3 configuration.

This module defines immutable value objects for S3-related configurations
used in the console_link application.
"""

from dataclasses import dataclass
from typing import Optional

from console_link.domain.exceptions.common_errors import ValidationError


@dataclass(frozen=True)
class S3Config:
    """Configuration for S3 storage.
    
    This immutable value object encapsulates S3 configuration details.
    """
    repo_uri: str
    region: str
    role_arn: Optional[str] = None
    endpoint: Optional[str] = None
    
    def __post_init__(self):
        """Validate S3 configuration."""
        if not self.repo_uri:
            raise ValidationError("S3 repo_uri cannot be empty")
        
        if not self.region:
            raise ValidationError("S3 region cannot be empty")
        
        if not self._is_valid_s3_uri(self.repo_uri):
            raise ValidationError(f"Invalid S3 URI format: {self.repo_uri}")
        
        if self.endpoint and not self._is_valid_endpoint(self.endpoint):
            raise ValidationError(f"Invalid S3 endpoint format: {self.endpoint}")
    
    def _is_valid_s3_uri(self, uri: str) -> bool:
        """Validate S3 URI format."""
        # Basic validation - should start with s3:// or s3a://
        return uri.startswith(("s3://", "s3a://"))
    
    def _is_valid_endpoint(self, endpoint: str) -> bool:
        """Validate endpoint format."""
        # Basic validation - should be a URL
        return endpoint.startswith(("http://", "https://"))
    
    @classmethod
    def from_dict(cls, data: dict) -> "S3Config":
        """Create an S3Config from a dictionary."""
        return cls(
            repo_uri=data.get("repo_uri", data.get("s3_repo_uri", "")),
            region=data.get("region", data.get("aws_region", data.get("s3_region", ""))),
            role_arn=data.get("role_arn", data.get("role", data.get("s3_role_arn"))),
            endpoint=data.get("endpoint", data.get("s3_endpoint"))
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "repo_uri": self.repo_uri,
            "region": self.region,
        }
        if self.role_arn:
            result["role_arn"] = self.role_arn
        if self.endpoint:
            result["endpoint"] = self.endpoint
        return result


@dataclass(frozen=True)
class FileSystemConfig:
    """Configuration for filesystem-based storage.
    
    This immutable value object encapsulates filesystem configuration details.
    """
    repo_path: str
    
    def __post_init__(self):
        """Validate filesystem configuration."""
        if not self.repo_path:
            raise ValidationError("Filesystem repo_path cannot be empty")
        
        if not self._is_valid_path(self.repo_path):
            raise ValidationError(f"Invalid filesystem path: {self.repo_path}")
    
    def _is_valid_path(self, path: str) -> bool:
        """Validate filesystem path format."""
        # Basic validation - should be an absolute path
        return path.startswith("/")
    
    @classmethod
    def from_dict(cls, data: dict) -> "FileSystemConfig":
        """Create a FileSystemConfig from a dictionary."""
        return cls(
            repo_path=data.get("repo_path", data.get("file_system_repo_path", ""))
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "repo_path": self.repo_path
        }
