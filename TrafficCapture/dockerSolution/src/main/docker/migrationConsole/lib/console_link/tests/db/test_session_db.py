import pytest
from datetime import datetime
from unittest.mock import patch
from console_link.db.session_db import (
    all_sessions, find_session, create_session, update_session, delete_session, existence_check,
    SessionNotFound, SessionUnreadable, SessionAlreadyExists, SessionNameLengthInvalid,
    SessionNameContainsInvalidCharacters
)
from console_link.models.session import Session
from console_link.environment import Environment


@pytest.fixture
def mock_db():
    with patch('console_link.db.session_db._DB') as mock_db:
        with patch('console_link.db.session_db._TABLE') as mock_table:
            with patch('console_link.db.session_db._QUERY') as mock_query:
                yield mock_db, mock_table, mock_query


@pytest.fixture
def valid_session():
    return Session(
        name="test-session",
        created=datetime.now(),
        updated=datetime.now(),
        env=Environment(config={"target_cluster": {"endpoint": "http://test", "no_auth": {}}})
    )


def test_all_sessions(mock_db):
    _, mock_table, _ = mock_db
    mock_table.all.return_value = [
        {"name": "session1", "created": datetime.now().isoformat(), "updated": datetime.now().isoformat(), "env": {}},
        {"name": "session2", "created": datetime.now().isoformat(), "updated": datetime.now().isoformat(), "env": {}}
    ]
    
    result = all_sessions()
    assert len(result) == 2
    assert all(isinstance(s, Session) for s in result)
    mock_table.all.assert_called_once()


def test_find_session_existing(mock_db):
    _, mock_table, mock_query = mock_db
    session_data = {
        "name": "test-session", 
        "created": datetime.now().isoformat(), 
        "updated": datetime.now().isoformat(), 
        "env": {}
    }
    mock_table.get.return_value = session_data
    
    result = find_session("test-session")
    assert result == session_data
    mock_table.get.assert_called_once()


def test_find_session_nonexistent(mock_db):
    _, mock_table, _ = mock_db
    mock_table.get.return_value = None
    
    result = find_session("nonexistent")
    assert result is None
    mock_table.get.assert_called_once()


def test_create_session_valid(mock_db, valid_session):
    _, mock_table, mock_query = mock_db
    mock_table.get.return_value = None
    
    create_session(valid_session)
    mock_table.insert.assert_called_once_with(valid_session.model_dump())


def test_create_session_already_exists(mock_db, valid_session):
    _, mock_table, mock_query = mock_db
    mock_table.get.return_value = {"name": valid_session.name}
    
    with pytest.raises(SessionAlreadyExists):
        create_session(valid_session)
    mock_table.insert.assert_not_called()


def test_create_session_invalid_name_length_empty(mock_db):
    invalid_session = Session(
        name="",  # Empty name
        created=datetime.now(),
        updated=datetime.now(),
        env=None
    )
    
    with pytest.raises(SessionNameLengthInvalid):
        create_session(invalid_session)


def test_create_session_invalid_name_length_too_long(mock_db):
    invalid_session = Session(
        name="a" * 51,  # Name > 50 characters
        created=datetime.now(),
        updated=datetime.now(),
        env=None
    )
    
    with pytest.raises(SessionNameLengthInvalid):
        create_session(invalid_session)


def test_create_session_invalid_name_chars(mock_db):
    invalid_session = Session(
        name="invalid/name",  # Contains invalid character
        created=datetime.now(),
        updated=datetime.now(),
        env=None
    )
    
    with pytest.raises(SessionNameContainsInvalidCharacters):
        create_session(invalid_session)


def test_update_session(mock_db, valid_session):
    _, mock_table, mock_query = mock_db
    
    with patch('console_link.db.session_db.datetime') as mock_datetime:
        current_time = datetime.now()
        mock_datetime.now.return_value = current_time
        mock_datetime.UTC = None
        
        update_session(valid_session)
        
        # Check the session's updated timestamp was set to current time
        mock_table.update.assert_called_once()
        # Get the first positional argument from the call
        called_args = mock_table.update.call_args[0][0]
        # The model_dump serializes datetime to ISO string, so we verify it was updated
        assert called_args["updated"] is not valid_session.updated


def test_delete_session_existing(mock_db):
    _, mock_table, mock_query = mock_db
    mock_table.remove.return_value = [1]  # Indicates successful removal
    
    delete_session("test-session")
    mock_table.remove.assert_called_once()


def test_delete_session_nonexistent(mock_db):
    _, mock_table, mock_query = mock_db
    mock_table.remove.return_value = []  # Indicates nothing was removed
    
    with pytest.raises(SessionNotFound):
        delete_session("nonexistent")
    mock_table.remove.assert_called_once()


def test_existence_check_valid():
    session_data = {
        "name": "test-session", 
        "created": datetime.now().isoformat(), 
        "updated": datetime.now().isoformat(), 
        "env": {}
    }
    
    result = existence_check(session_data)
    assert isinstance(result, Session)
    assert result.name == "test-session"


def test_existence_check_none():
    with pytest.raises(SessionNotFound):
        existence_check(None)


def test_existence_check_invalid():
    with pytest.raises(SessionUnreadable):
        existence_check({"invalid": "data"})  # Missing required fields
