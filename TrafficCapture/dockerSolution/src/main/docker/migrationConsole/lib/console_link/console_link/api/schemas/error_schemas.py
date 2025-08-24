"""Pydantic schemas for error responses."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes."""
    # Client errors (4xx)
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"
    
    # Domain-specific errors
    CLUSTER_UNREACHABLE = "CLUSTER_UNREACHABLE"
    SNAPSHOT_NOT_FOUND = "SNAPSHOT_NOT_FOUND"
    BACKFILL_ALREADY_RUNNING = "BACKFILL_ALREADY_RUNNING"
    INVALID_CLUSTER_CONFIG = "INVALID_CLUSTER_CONFIG"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    OPERATION_TIMEOUT = "OPERATION_TIMEOUT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Specific error code")
    
    class Config:
        orm_mode = True
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: str = Field(..., description="Error timestamp in ISO format")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    
    class Config:
        orm_mode = True
        from_attributes = True
        schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "snapshot_name",
                        "message": "Field is required",
                        "code": "missing"
                    }
                ],
                "request_id": "req-123456",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/api/v1/snapshot"
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-level details."""
    error: ErrorCode = Field(ErrorCode.VALIDATION_ERROR, const=True)
    
    class Config:
        schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "endpoint",
                        "message": "Must start with http:// or https://",
                        "code": "invalid_format"
                    },
                    {
                        "field": "auth_method",
                        "message": "Invalid authentication method",
                        "code": "invalid_choice"
                    }
                ],
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class NotFoundErrorResponse(ErrorResponse):
    """Not found error response."""
    error: ErrorCode = Field(ErrorCode.NOT_FOUND, const=True)
    
    class Config:
        schema_extra = {
            "example": {
                "error": "NOT_FOUND",
                "message": "Resource not found",
                "timestamp": "2024-01-01T12:00:00Z",
                "path": "/api/v1/cluster/unknown-cluster"
            }
        }


class ConflictErrorResponse(ErrorResponse):
    """Conflict error response."""
    error: ErrorCode = Field(ErrorCode.CONFLICT, const=True)
    conflict_type: Optional[str] = Field(None, description="Type of conflict")
    existing_resource: Optional[Dict[str, Any]] = Field(None, description="Existing resource info")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "CONFLICT",
                "message": "Backfill already running for these indices",
                "conflict_type": "resource_busy",
                "existing_resource": {
                    "backfill_id": "backfill-123",
                    "status": "running"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class UnauthorizedErrorResponse(ErrorResponse):
    """Unauthorized error response."""
    error: ErrorCode = Field(ErrorCode.UNAUTHORIZED, const=True)
    auth_type: Optional[str] = Field(None, description="Expected authentication type")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "UNAUTHORIZED",
                "message": "Authentication required",
                "auth_type": "Bearer",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ForbiddenErrorResponse(ErrorResponse):
    """Forbidden error response."""
    error: ErrorCode = Field(ErrorCode.FORBIDDEN, const=True)
    required_permissions: Optional[List[str]] = Field(None, description="Required permissions")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "FORBIDDEN",
                "message": "Insufficient permissions",
                "required_permissions": ["cluster:admin", "snapshot:create"],
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class InternalErrorResponse(ErrorResponse):
    """Internal server error response."""
    error: ErrorCode = Field(ErrorCode.INTERNAL_ERROR, const=True)
    error_id: Optional[str] = Field(None, description="Error ID for support reference")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "error_id": "err-abc123",
                "request_id": "req-123456",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Service unavailable error response."""
    error: ErrorCode = Field(ErrorCode.SERVICE_UNAVAILABLE, const=True)
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "SERVICE_UNAVAILABLE",
                "message": "Service temporarily unavailable",
                "retry_after": 60,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit error response."""
    error: ErrorCode = Field(ErrorCode.TOO_MANY_REQUESTS, const=True)
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset_at: str = Field(..., description="When the rate limit resets")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "TOO_MANY_REQUESTS",
                "message": "Rate limit exceeded",
                "limit": 100,
                "remaining": 0,
                "reset_at": "2024-01-01T13:00:00Z",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
