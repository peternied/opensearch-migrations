import logging
from fastapi import HTTPException, APIRouter, Body

from console_link.api.sessions import http_safe_find_session
from console_link.db import session_db
from console_link.models.cluster import AuthMethod, BasicAuthArn, Cluster, ClusterInfo, NoAuth, SigV4Auth

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

clusters_router = APIRouter(
    prefix="/clusters",
    tags=["clusters"],
)


def convert_cluster_to_api_model(cluster: Cluster) -> ClusterInfo:
    """
    Converts an internal Cluster model to the API ClusterInfo model.
    """
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Extract protocol from endpoint
    protocol = "https" if cluster.endpoint.startswith("https://") else "http"
    
    if cluster.auth_type and cluster.auth_type == AuthMethod.BASIC_AUTH:
        if cluster.auth_details and "user_secret_arn" in cluster.auth_details:
            auth = BasicAuthArn(user_secret_arn=cluster.auth_details["user_secret_arn"])
        else:
            logger.warning("Detected raw username/password authentication information,"
                           "returning as if no arn was available")
            auth = BasicAuthArn(user_secret_arn="")
    elif cluster.auth_type and cluster.auth_type == AuthMethod.SIGV4:
        service_name, region_name = cluster._get_sigv4_details()
        auth = SigV4Auth(region=region_name, service=service_name)
    else:
        auth = NoAuth()
    
    # Create and return the ClusterInfo model
    return ClusterInfo(
        endpoint=cluster.endpoint,
        protocol=protocol,
        enable_tls_verification=not cluster.allow_insecure,
        auth=auth,
        version_override=cluster.version,
    )


def _normalize_endpoint(endpoint: str, protocol: str | None) -> str:
    """
    Ensure the endpoint string includes a scheme. If protocol is provided
    and endpoint lacks a scheme, prefix with '<protocol>://'.
    """
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    # Fallback to https if protocol missing
    scheme = (protocol or "https").lower()
    if scheme not in ("http", "https"):
        scheme = "https"
    return f"{scheme}://{endpoint}"


def convert_api_model_to_cluster(info: ClusterInfo) -> Cluster:
    """
    Converts API ClusterInfo into the internal Cluster by constructing
    the expected config dict for Cluster(config, client_options=None).
    """
    if info is None:
        raise HTTPException(status_code=400, detail="Cluster payload is required")

    endpoint = _normalize_endpoint(info.endpoint, info.protocol)

    # Build auth block
    auth_block: dict
    if isinstance(info.auth, BasicAuthArn):
        auth_block = {"basic_auth": {"user_secret_arn": info.auth.user_secret_arn or ""}}
    elif isinstance(info.auth, SigV4Auth):
        auth_block = {"sigv4": {"service": info.auth.service, "region": info.auth.region}}
    elif isinstance(info.auth, NoAuth) or info.auth is None:
        # Presence of 'no_auth' key selects NO_AUTH
        auth_block = {"no_auth": {}}
    else:
        raise HTTPException(status_code=400, detail="Unsupported auth type")

    allow_insecure = not bool(info.enable_tls_verification)

    config = {
        "endpoint": endpoint,
        "version": info.version_override,
        "allow_insecure": allow_insecure,
        **auth_block,
    }

    try:
        return Cluster(config=config, client_options=None)
    except ValueError as e:
        # Raised by Validator(SCHEMA) path
        # e.args may contain (message, errors); stringify safely
        msg = "; ".join(str(a) for a in e.args if a)
        raise HTTPException(status_code=400, detail=f"Invalid cluster definition: {msg}")


@clusters_router.get("/source", response_model=ClusterInfo, operation_id="clusterSource")
def get_source_cluster(session_name: str):
    session = http_safe_find_session(session_name)
    
    if not session.env or not session.env.source_cluster:
        raise HTTPException(status_code=404, detail="Source cluster not defined for this session")
    
    return convert_cluster_to_api_model(session.env.source_cluster)


@clusters_router.get("/target", response_model=ClusterInfo, operation_id="clusterTarget")
def get_target_cluster(session_name: str):
    session = http_safe_find_session(session_name)
    if not session.env or not session.env.target_cluster:
        raise HTTPException(status_code=404, detail="Target cluster not defined for this session")
    
    return convert_cluster_to_api_model(session.env.target_cluster)


@clusters_router.put("/source", response_model=ClusterInfo, operation_id="clusterSourceSet")
def set_source_cluster(
    session_name: str,
    cluster_info: ClusterInfo = Body(..., description="Source cluster configuration"),
):
    session = http_safe_find_session(session_name)
    if not session.env:
        raise HTTPException(status_code=400, detail="Session environment is not initialized")

    internal_cluster = convert_api_model_to_cluster(cluster_info)
    session.env.source_cluster = internal_cluster
    session_db.update_session(session)

    return convert_cluster_to_api_model(session.env.source_cluster)


@clusters_router.put(
    "/target",
    response_model=ClusterInfo,
    operation_id="clusterTargetSet",
    summary="Set or replace the target cluster for a session",
)
def set_target_cluster(
    session_name: str,
    cluster_info: ClusterInfo = Body(..., description="Target cluster configuration"),
):
    session = http_safe_find_session(session_name)
    if not session.env:
        raise HTTPException(status_code=400, detail="Session environment is not initialized")

    internal_cluster = convert_api_model_to_cluster(cluster_info)
    session.env.target_cluster = internal_cluster
    session_db.update_session(session)

    return convert_cluster_to_api_model(session.env.target_cluster)
