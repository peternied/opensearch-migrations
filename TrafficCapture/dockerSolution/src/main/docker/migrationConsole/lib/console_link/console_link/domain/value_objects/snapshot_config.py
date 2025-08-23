"""Value objects for snapshot configuration.

This module defines immutable value objects for snapshot-related configurations.
"""

from dataclasses import dataclass
from typing import Optional

from console_link.models.utils import DEFAULT_SNAPSHOT_REPO_NAME

DEFAULT_REPO = "migration_assistant_repo"

@dataclass(frozen=True)
class SnapshotConfig:
    """Base configuration for snapshots.
    
    All snapshot configurations contain these common fields.
    """
    snapshot_name: str
    snapshot_repo_name: str = DEFAULT_SNAPSHOT_REPO_NAME
    otel_endpoint: Optional[str] = None
    
    def __post_init__(self):
        if not self.snapshot_name:
            raise ValueError("snapshot_name cannot be empty")
        if not self.snapshot_repo_name:
            raise ValueError("snapshot_repo_name cannot be empty")


@dataclass(frozen=True)
class S3SnapshotConfig:
    """Configuration for S3-based snapshots."""
    # Required fields
    snapshot_name: str
    repo_uri: str
    aws_region: str
    # Optional fields
    snapshot_repo_name: str = DEFAULT_SNAPSHOT_REPO_NAME
    otel_endpoint: Optional[str] = None
    role_arn: Optional[str] = None
    endpoint: Optional[str] = None
    
    def __post_init__(self):
        if not self.snapshot_name:
            raise ValueError("snapshot_name cannot be empty")
        if not self.snapshot_repo_name:
            raise ValueError("snapshot_repo_name cannot be empty")
        if not self.repo_uri:
            raise ValueError("repo_uri cannot be empty")
        if not self.aws_region:
            raise ValueError("aws_region cannot be empty")


@dataclass(frozen=True)
class FileSystemSnapshotConfig:
    """Configuration for filesystem-based snapshots."""
    # Required fields
    snapshot_name: str
    repo_path: str
    # Optional fields
    snapshot_repo_name: str = DEFAULT_SNAPSHOT_REPO_NAME
    otel_endpoint: Optional[str] = None
    
    def __post_init__(self):
        if not self.snapshot_name:
            raise ValueError("snapshot_name cannot be empty")
        if not self.snapshot_repo_name:
            raise ValueError("snapshot_repo_name cannot be empty")
        if not self.repo_path:
            raise ValueError("repo_path cannot be empty")
