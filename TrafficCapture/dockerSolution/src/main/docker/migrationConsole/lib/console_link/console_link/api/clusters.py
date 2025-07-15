from logging import log
import logging
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from console_link.models.cluster import Cluster, HttpMethod
from console_link.models.snapshot import Snapshot
# import your existing funcs — change this path to wherever you put them
from console_link.middleware.clusters import (
    call_api,
    cat_indices,
    connection_check,
    run_test_benchmarks,
    clear_indices,
)

router = APIRouter(
    prefix="/cluster",
    tags=["cluster"],
)


class ClusterConfig(BaseModel):
    endpoint: str = Field(description="The address of the cluster.")
    auth_type: Literal['basic_auth', 'no_auth', 'sigv4']
    auth_details: Optional[Dict[str, Any]] = None
    allow_insecure: Optional[bool] = False


class CallApiRequest(BaseModel):
    cluster: ClusterConfig
    path: str
    method: HttpMethod = HttpMethod.GET
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[float] = None
    raise_error: bool = False


class CallApiResponse(BaseModel):
    status_code: int
    content: Any


class CatIndicesRequest(BaseModel):
    cluster: ClusterConfig
    refresh: Optional[bool] = False


class CatIndicesResponse(BaseModel):
    result: Any


class ConnectionCheckRequest(BaseModel):
    cluster: ClusterConfig


class ConnectionCheckResponse(BaseModel):
    connection_message: str
    connection_established: bool
    cluster_version: Optional[str] = None


class GenericResponse(BaseModel):
    message: str


@router.post("/call_api", response_model=CallApiResponse)
def call_api_api(req: CallApiRequest):
    c = Cluster(dict[str, Any](
        endpoint=req.cluster.endpoint,
        auth_type=req.cluster.auth_type,
        auth_details=req.cluster.auth_details or {},
        allow_insecure=req.cluster.allow_insecure,
    ))
    try:
        r = call_api(
            cluster=c,
            path=req.path,
            method=req.method,
            data=req.data,
            headers=req.headers,
            timeout=req.timeout,
            raise_error=req.raise_error,
        )
        return CallApiResponse(status_code=r.status_code, content=r.json() if hasattr(r, "json") else r.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cat_indices", response_model=CatIndicesResponse)
def cat_indices_api(req: CatIndicesRequest):
    logging.info(f"cat indices with: {req.cluster.dict()}")
    c = Cluster(req.cluster.dict())
    try:
        res = cat_indices(c, refresh=req.refresh or True, as_json=True)
        return CatIndicesResponse(result=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connection_check", response_model=ConnectionCheckResponse)
def connection_check_api(req: ConnectionCheckRequest):
    c = Cluster(req.cluster.dict())
    result = connection_check(c)
    return ConnectionCheckResponse(
        connection_message=result.connection_message,
        connection_established=result.connection_established,
        cluster_version=result.cluster_version,
    )


@router.post("/run_benchmarks", response_model=GenericResponse)
def run_benchmarks_api(req: ConnectionCheckRequest):
    c = Cluster(**req.cluster.dict())
    try:
        run_test_benchmarks(c)
        return GenericResponse(message="Benchmarks kicked off")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear_indices", response_model=CatIndicesResponse)
def clear_indices_api(req: CatIndicesRequest):
    c = Cluster(**req.cluster.dict())
    try:
        res = clear_indices(c)
        return CatIndicesResponse(result=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

