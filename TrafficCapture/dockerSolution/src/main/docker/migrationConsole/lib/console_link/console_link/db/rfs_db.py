from datetime import datetime, UTC
from functools import wraps
from threading import RLock
from pydantic import BaseModel, field_validator, field_serializer
from tinydb import TinyDB, Query

from console_link.models.session import Session

DB_PATH = "rfs_db.json"
db = TinyDB(DB_PATH)
_workflows_table = db.table("worfklows")
_LOCK = RLock()
rfs_query = Query()


class RfsWorkflowEntry(BaseModel):
    """Database storage model for rfs workflow executions."""
    session_name: str
    workflow: str
    timestamp: datetime
    started: datetime
    finished: datetime

    @field_serializer('started', 'finished', 'timestamp')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    @field_validator('started', 'finished', 'timestamp', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


# Helper decorator to keep code tidy
def with_lock(fn):
    @wraps(fn)
    def _wrapped(*args, **kwargs):
        with _LOCK:
            return fn(*args, **kwargs)
    return _wrapped


@with_lock
def get_latest(session_name: str) -> RfsWorkflowEntry:
    results = _workflows_table.get(rfs_query.name == session_name)
    
    if not results or len(results) == 0:
        raise RfsWorkflowNotAvailable

    latest_item = sorted(results, key=lambda x: x["timestamp"], reverse=True)[0]
    return RfsWorkflowEntry.model_validate(latest_item)


@with_lock
def update_entry(entry: RfsWorkflowEntry):
    entry.updated = datetime.now(UTC)
    _workflows_table.update(entry.model_dump(), rfs_query.name == entry.name)


@with_lock
def create_entry(entry: RfsWorkflowEntry):
    _workflows_table.insert(entry.model_dump())


@with_lock
def clear_all():
    _workflows_table.truncate()


class RfsWorkflowNotAvailable(Exception):
    pass
