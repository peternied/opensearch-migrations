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
    auth_method: Optional[AuthMethod] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "AuthConfig":
        """Create an AuthConfig from a dictionary.
        
        This factory method determines which specific auth config to create
        based on the auth_method in the data.
        """
        if not data:
            return NoAuthConfig()
        
        auth_method = data.get("auth_method")
        if auth_method == AuthMethod.NO_AUTH.value or auth_method == AuthMethod.NO_AUTH:
            return NoAuthConfig()
        elif auth_method == AuthMethod.BASIC_AUTH.value or auth_method == AuthMethod.BASIC_AUTH:
            return BasicAuthConfig(
                username=data.get("username"),
                password=data.get("password"),
                user_secret_arn=data.get("user_secret_arn")
            )
        elif auth_method == AuthMethod.SIGV4.value or auth_method == AuthMethod.SIGV4:
            return SigV4AuthConfig(
                region=data.get("region"),
                service=data.get("service", "es")
            )
        else:
            # Default to no auth if method is not recognized
            return NoAuthConfig()
    
    def to_dict(self) -> dict:
        """Convert the auth config to a dictionary.
        
        This base implementation should be overridden by subclasses.
        """
        return {"auth_method": self.auth_method.value if self.auth_method else None}


@dataclass(frozen=True)
class NoAuthConfig(AuthConfig):
    """Configuration for no authentication."""
    auth_method: AuthMethod = AuthMethod.NO_AUTH
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"auth_method": self.auth_method.value}


@dataclass(frozen=True)
class BasicAuthConfig(AuthConfig):
    """Configuration for basic authentication.
    
    Can be configured with either username/password directly or
    with a secret ARN that contains the credentials.
    """
    auth_method: AuthMethod = AuthMethod.BASIC_AUTH
    username: Optional[str] = None
    password: Optional[str] = None
    user_secret_arn: Optional[str] = None
    
    def __post_init__(self):
        # Validation
        has_user_pass = self.username is not None and self.password is not None
        has_secret = self.user_secret_arn is not None
        
        if has_user_pass and has_secret:
            raise ValueError("Cannot provide both (username + password) and user_secret_arn")
        elif has_user_pass and (self.username == "" or self.password == ""):
            raise ValueError("Both username and password must be non-empty")
        elif not has_user_pass and not has_secret:
            raise ValueError("Must provide either (username + password) or user_secret_arn")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {"auth_method": self.auth_method.value}
        if self.username is not None:
            result["username"] = self.username
        if self.password is not None:
            result["password"] = self.password
        if self.user_secret_arn is not None:
            result["user_secret_arn"] = self.user_secret_arn
        return result


@dataclass(frozen=True)
class SigV4AuthConfig(AuthConfig):
    """Configuration for AWS Signature Version 4 authentication."""
    auth_method: AuthMethod = AuthMethod.SIGV4
    region: Optional[str] = None
    service: str = "es"  # Default to Elasticsearch service
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {"auth_method": self.auth_method.value}
        if self.region is not None:
            result["region"] = self.region
        result["service"] = self.service
        return result


@dataclass(frozen=True)
class AuthDetails:
    """Resolved authentication details (e.g., after fetching from secrets manager)."""
    username: str
    password: str
