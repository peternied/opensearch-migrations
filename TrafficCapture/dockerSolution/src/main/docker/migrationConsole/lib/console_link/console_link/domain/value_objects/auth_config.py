"""Value objects for authentication configuration.

This module defines immutable value objects for various authentication methods
used in the console_link application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AuthMethod(Enum):
    """Enumeration of supported authentication methods."""
    NO_AUTH = "no_auth"
    BASIC_AUTH = "basic_auth"
    SIGV4 = "sigv4"


@dataclass(frozen=True)
class AuthConfig:
    """Base class for authentication configuration.
    
    All auth config classes should inherit from this base class.
    The frozen=True makes instances immutable.
    """
    auth_method: AuthMethod


@dataclass(frozen=True)
class NoAuthConfig(AuthConfig):
    """Configuration for no authentication."""
    
    def __post_init__(self):
        object.__setattr__(self, 'auth_method', AuthMethod.NO_AUTH)


@dataclass(frozen=True)
class BasicAuthConfig(AuthConfig):
    """Configuration for basic authentication.
    
    Can be configured with either username/password directly or
    with a secret ARN that contains the credentials.
    """
    username: Optional[str] = None
    password: Optional[str] = None
    user_secret_arn: Optional[str] = None
    
    def __post_init__(self):
        object.__setattr__(self, 'auth_method', AuthMethod.BASIC_AUTH)
        
        # Validation
        has_user_pass = self.username is not None and self.password is not None
        has_secret = self.user_secret_arn is not None
        
        if has_user_pass and has_secret:
            raise ValueError("Cannot provide both (username + password) and user_secret_arn")
        elif has_user_pass and (self.username == "" or self.password == ""):
            raise ValueError("Both username and password must be non-empty")
        elif not has_user_pass and not has_secret:
            raise ValueError("Must provide either (username + password) or user_secret_arn")


@dataclass(frozen=True)
class SigV4AuthConfig(AuthConfig):
    """Configuration for AWS Signature Version 4 authentication."""
    region: Optional[str] = None
    service: str = "es"  # Default to Elasticsearch service
    
    def __post_init__(self):
        object.__setattr__(self, 'auth_method', AuthMethod.SIGV4)
        if self.service is None:
            object.__setattr__(self, 'service', "es")


@dataclass(frozen=True)
class AuthDetails:
    """Resolved authentication details (e.g., after fetching from secrets manager)."""
    username: str
    password: str
