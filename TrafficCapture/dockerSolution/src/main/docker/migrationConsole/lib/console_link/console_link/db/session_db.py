import re
from datetime import datetime, UTC
from typing import Any, List, Optional
from functools import wraps
from threading import RLock
from tinydb import TinyDB, Query

from console_link.models.session import Session

DB_PATH = "sessions_db.json"
db = TinyDB(DB_PATH)
_sessions_table = db.table("sessions")
_LOCK = RLock()


# Helper decorator to keep code tidy
def with_lock(fn):
    @wraps(fn)
    def _wrapped(*args, **kwargs):
        with _LOCK:
            return fn(*args, **kwargs)
    return _wrapped


session_query = Query()


@with_lock
def all_sessions() -> List[Session]:
    sessions = _sessions_table.all()
    return [Session.model_validate(session) for session in sessions]


@with_lock
def find_session(session_name: str) -> Optional[dict]:
    return _sessions_table.get(session_query.name == session_name)


@with_lock
def create_session(session: Session):
    def is_url_safe(name: str) -> bool:
        return re.match(r'^[a-zA-Z0-9_\-]+$', name) is not None

    def unexpected_length(name: str) -> bool:
        return len(name) <= 0 or len(name) > 50

    if unexpected_length(session.name):
        raise SessionNameLengthInvalid()

    if not is_url_safe(session.name):
        raise SessionNameContainsInvalidCharacters()

    # Existence check and insert protected by the same lock for atomicity
    if _sessions_table.get(session_query.name == session.name):
        raise SessionAlreadyExists()

    _sessions_table.insert(session.model_dump())


@with_lock
def update_session(session: Session):
    session.updated = datetime.now(UTC)
    _sessions_table.update(session.model_dump(), session_query.name == session.name)


@with_lock
def delete_session(session_name: str):
    removed = _sessions_table.remove(session_query.name == session_name)
    if not removed:
        raise SessionNotFound()


@with_lock
def existence_check(session: Any) -> Session:
    if not session:
        raise SessionNotFound()
    try:
        return Session.model_validate(session)
    except Exception:
        raise SessionUnreadable()


class SessionNotFound(Exception):
    pass


class SessionUnreadable(Exception):
    pass


class SessionAlreadyExists(Exception):
    pass


class SessionNameLengthInvalid(Exception):
    pass


class SessionNameContainsInvalidCharacters(Exception):
    pass
