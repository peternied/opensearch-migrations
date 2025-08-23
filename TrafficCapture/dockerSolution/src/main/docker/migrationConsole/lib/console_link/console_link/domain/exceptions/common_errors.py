"""Base exception classes for the migration assistant domain layer.

This module defines the exception hierarchy used throughout the application.
All domain-specific exceptions should inherit from these base classes.
"""


class MigrationAssistantError(Exception):
    """Base exception for all errors.
    
    All custom exceptions in the application should inherit from this class.
    """
    pass


class ValidationError(MigrationAssistantError):
    """Raised when input validation fails.
    
    This exception is used when data doesn't meet the required constraints
    or business rules.
    """
    pass


class NotFoundError(MigrationAssistantError):
    """Raised when a requested resource cannot be found.
    
    This exception is used when attempting to access a resource
    (entity, file, etc.) that doesn't exist.
    """
    pass


class OperationError(MigrationAssistantError):
    """Raised when an operation fails to complete.
    
    This is a general exception for operation failures that don't
    fit into more specific categories.
    """
    pass


class ConfigurationError(MigrationAssistantError):
    """Raised when there's an issue with configuration.
    
    This exception is used for invalid or missing configuration values.
    """
    pass


class AuthenticationError(MigrationAssistantError):
    """Raised when authentication fails.
    
    This exception is used when credentials are invalid or missing.
    """
    pass


class AuthorizationError(MigrationAssistantError):
    """Raised when authorization fails.
    
    This exception is used when a user lacks permissions for an operation.
    """
    pass


class ExternalServiceError(MigrationAssistantError):
    """Raised when an external service call fails.
    
    This exception is used when calls to external services (APIs, databases, etc.)
    fail or return unexpected results.
    """
    pass


class TimeoutError(MigrationAssistantError):
    """Raised when an operation times out.
    
    This exception is used when an operation exceeds its allowed time limit.
    """
    pass


class ConcurrencyError(MigrationAssistantError):
    """Raised when there's a concurrency conflict.
    
    This exception is used for race conditions, lock failures, or
    other concurrency-related issues.
    """
    pass


class DataIntegrityError(MigrationAssistantError):
    """Raised when data integrity is compromised.
    
    This exception is used when data is corrupted, inconsistent,
    or violates integrity constraints.
    """
    pass
