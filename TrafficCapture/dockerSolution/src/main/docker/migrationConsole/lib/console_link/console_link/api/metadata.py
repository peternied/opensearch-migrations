from typing import Optional, Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, root_validator, Extra

from console_link.models.schema_tools import list_schema   # for reference
from console_link.models.metadata import SCHEMA, Metadata             # your Cerberus schema
from console_link.models.cluster import Cluster             # your cluster model
from console_link.models.snapshot import Snapshot           # your snapshot base class
from console_link.models.utils import ExitCode
from console_link.middleware.metadata import migrate as migrate_fn, evaluate as eval_fn

from cerberus import Validator

metadata_router = APIRouter(
    prefix="/metadata",
    responses={404: {"description": "Not found"}},
)

class MetadataConfig(BaseModel):
    # allow everything that SCHEMA expects plus nothing else is forbidden:
    class Config:
        extra = Extra.forbid

    @root_validator(pre=True)
    def cerberus_validate(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        v = Validator(SCHEMA)
        if not v.validate(values):
            # bubble up Cerberus errors as a 422
            raise ValueError(v.errors)
        return values

class MetadataRequest(BaseModel):
    config: MetadataConfig
    cluster: Dict[str, Any]               # “target_cluster” fields you need
    snapshot: Optional[Dict[str, Any]]    # fit your S3Snapshot / FileSystemSnapshot

class MessageResponse(BaseModel):
    message: str

@metadata_router.post("/evaluate", response_model=MessageResponse)
def evaluate_endpoint(req: MetadataRequest):
    try:
        target_cluster = Cluster(**req.cluster)
        snap: Optional[Snapshot] = (
            Snapshot.from_dict(req.snapshot) if req.snapshot else None
        )
        meta = Metadata(req.config.model_dump(), target_cluster, snap)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    exit_code, msg = eval_fn(meta, [])
    if exit_code != ExitCode.SUCCESS:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}