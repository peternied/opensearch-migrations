from datetime import datetime
from pydantic import BaseModel, field_validator, field_serializer
from threading import RLock
from tinydb import TinyDB, Query

from console_link.db.utils import with_lock

_DB = TinyDB("workflows_db.json")
_TABLE = _DB.table("workflows")
_LOCK = RLock()
_QUERY = Query()


class WorkflowEntry(BaseModel):
    """Database storage model for scheduled workflow executions."""
    session_name: str
    workflow: str
    timestamp: datetime

    @field_serializer('timestamp')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    @field_validator('timestamp', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


@with_lock(_LOCK)
def get_latest(session_name: str) -> WorkflowEntry:
    results = _TABLE.get(_QUERY.session_name == session_name)
    
    if not results or len(results) == 0:
        raise WorkflowNotAvailable

    latest_item = sorted(results, key=lambda x: x["timestamp"], reverse=True)[0]
    return WorkflowEntry.model_validate(latest_item)


@with_lock(_LOCK)
def create_entry(entry: WorkflowEntry):
    _TABLE.insert(entry.model_dump())


@with_lock(_LOCK)
def clear_all():
    _TABLE.truncate()


class WorkflowNotAvailable(Exception):
    pass
