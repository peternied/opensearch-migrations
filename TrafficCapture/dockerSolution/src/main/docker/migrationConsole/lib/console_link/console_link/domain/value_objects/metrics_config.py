"""Value objects for metrics configuration.

This module defines immutable value objects for metrics-related configurations
used in the console_link application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from console_link.domain.exceptions.common_errors import ValidationError


class MetricsProvider(Enum):
    """Supported metrics providers."""
    CLOUDWATCH = "cloudwatch"
    PROMETHEUS = "prometheus"
    OTEL = "otel"


@dataclass(frozen=True)
class MetricsConfig:
    """Configuration for metrics collection and reporting.
    
    This immutable value object encapsulates metrics configuration details.
    """
    provider: MetricsProvider
    endpoint: Optional[str] = None
    namespace: Optional[str] = None
    
    def __post_init__(self):
        """Validate metrics configuration."""
        if not isinstance(self.provider, MetricsProvider):
            raise ValidationError(f"Invalid metrics provider: {self.provider}")
        
        # Provider-specific validation
        if self.provider == MetricsProvider.OTEL and not self.endpoint:
            raise ValidationError("OTEL provider requires an endpoint")
        
        if self.endpoint and not self._is_valid_endpoint(self.endpoint):
            raise ValidationError(f"Invalid metrics endpoint format: {self.endpoint}")
    
    def _is_valid_endpoint(self, endpoint: str) -> bool:
        """Validate endpoint format."""
        # Basic validation - should be a URL
        return endpoint.startswith(("http://", "https://", "grpc://"))
    
    @classmethod
    def from_dict(cls, data: dict) -> "MetricsConfig":
        """Create a MetricsConfig from a dictionary."""
        provider_str = data.get("provider", "cloudwatch")
        try:
            provider = MetricsProvider(provider_str)
        except ValueError:
            provider = MetricsProvider.CLOUDWATCH
        
        return cls(
            provider=provider,
            endpoint=data.get("endpoint", data.get("otel_endpoint")),
            namespace=data.get("namespace")
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "provider": self.provider.value,
        }
        if self.endpoint:
            result["endpoint"] = self.endpoint
        if self.namespace:
            result["namespace"] = self.namespace
        return result


@dataclass(frozen=True)
class CloudWatchConfig(MetricsConfig):
    """Configuration specific to CloudWatch metrics."""
    region: str = "us-east-1"
    
    def __post_init__(self):
        """Ensure provider is CloudWatch and validate configuration."""
        if self.provider != MetricsProvider.CLOUDWATCH:
            object.__setattr__(self, 'provider', MetricsProvider.CLOUDWATCH)
        super().__post_init__()
        
        if not self.region:
            raise ValidationError("CloudWatch region cannot be empty")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result["region"] = self.region
        return result


@dataclass(frozen=True)
class PrometheusConfig(MetricsConfig):
    """Configuration specific to Prometheus metrics."""
    port: int = 9090
    path: str = "/metrics"
    
    def __post_init__(self):
        """Ensure provider is Prometheus and validate configuration."""
        if self.provider != MetricsProvider.PROMETHEUS:
            object.__setattr__(self, 'provider', MetricsProvider.PROMETHEUS)
        super().__post_init__()
        
        if self.port < 1 or self.port > 65535:
            raise ValidationError(f"Port must be between 1 and 65535, got {self.port}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result["port"] = self.port
        result["path"] = self.path
        return result


@dataclass(frozen=True)
class OTelConfig(MetricsConfig):
    """Configuration specific to OpenTelemetry metrics."""
    service_name: str = "migration-assistant"
    protocol: str = "grpc"  # grpc or http/protobuf
    
    def __post_init__(self):
        """Ensure provider is OTEL and validate configuration."""
        if self.provider != MetricsProvider.OTEL:
            object.__setattr__(self, 'provider', MetricsProvider.OTEL)
        super().__post_init__()
        
        if self.protocol not in ("grpc", "http/protobuf"):
            raise ValidationError(f"Protocol must be 'grpc' or 'http/protobuf', got {self.protocol}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result["service_name"] = self.service_name
        result["protocol"] = self.protocol
        return result
