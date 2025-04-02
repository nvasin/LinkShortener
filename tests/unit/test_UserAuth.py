import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from app.api.authentication.UserAuth import get_current_user
from app.database.models.UserModel import User

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_request():
    class MockRequest:
        headers = {}
    return MockRequest()

def test_get_current_user_no_authorization_header(mock_request, mock_db):
    mock_request.headers = {}
    result = get_current_user(mock_request, mock_db)
    assert result is None

def test_get_current_user_invalid_token(mock_request, mock_db):
    mock_request.headers = {"Authorization": "invalid_token"}
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(mock_request, mock_db)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Invalid token"

def test_get_current_user_valid_token(mock_request, mock_db):
    mock_request.headers = {"Authorization": "valid_token"}
    mock_user = User(id=1, token="valid_token")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    result = get_current_user(mock_request, mock_db)
    assert result == mock_user