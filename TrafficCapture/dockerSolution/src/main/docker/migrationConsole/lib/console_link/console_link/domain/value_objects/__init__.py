"""Domain value objects for the migration assistant."""

from .auth_config import (
    AuthConfig,
    AuthDetails,
    AuthMethod,
    BasicAuthConfig,
    NoAuthConfig,
    SigV4AuthConfig,
)
from .container_config import (
    ContainerConfig,
    ContainerRuntime,
    DockerConfig,
    ECSConfig,
    KubernetesConfig,
)
from .metrics_config import (
    CloudWatchConfig,
    MetricsConfig,
    MetricsProvider,
    OTelConfig,
    PrometheusConfig,
)
from .s3_config import (
    FileSystemConfig,
    S3Config,
)
from .snapshot_config import (
    SnapshotConfig,
)

__all__ = [
    # Auth
    "AuthConfig",
    "AuthDetails",
    "AuthMethod",
    "BasicAuthConfig",
    "NoAuthConfig",
    "SigV4AuthConfig",
    # Container
    "ContainerConfig",
    "ContainerRuntime",
    "DockerConfig",
    "ECSConfig",
    "KubernetesConfig",
    # Metrics
    "CloudWatchConfig",
    "MetricsConfig",
    "MetricsProvider",
    "OTelConfig",
    "PrometheusConfig",
    # S3
    "FileSystemConfig",
    "S3Config",
    # Snapshot
    "SnapshotConfig",
]
