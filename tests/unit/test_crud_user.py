import pytest
import hashlib
from sqlalchemy.orm import Session
from app.crud.crud_user import get_user_by_email, create_user, authenticate_user
from app.database.models.UserModel import User
from app.api.schemas.UserSchema import UserCreate
from unittest.mock import MagicMock

@pytest.fixture
def db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "securepassword"
    }




def test_get_user_by_email(db_session):
    mock_user = User(email="test@example.com", hashed_password="hashedpassword", token="token")
    db_session.query().filter().first.return_value = mock_user

    result = get_user_by_email(db_session, "test@example.com")

    assert result == mock_user
    db_session.query().filter().first.assert_called_once()

def test_create_user(db_session, user_data):
    user_in = UserCreate(**user_data)

    result = create_user(db_session, user_in)

    assert result.email == user_data["email"]
    assert result.hashed_password is not None
    assert result.token is not None
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()

def test_authenticate_user(db_session, user_data):
    hashed_password = hashlib.sha256(user_data["password"].encode()).hexdigest()
    mock_user = User(email=user_data["email"], hashed_password=hashed_password, token="token")
    db_session.query().filter().first.return_value = mock_user

    result = authenticate_user(db_session, user_data["email"], user_data["password"])

    assert result == mock_user
    db_session.query().filter().first.assert_called_once()

def test_authenticate_user_invalid_password(db_session, user_data):
    correct_hashed_password = hashlib.sha256(user_data["password"].encode()).hexdigest()
    mock_user = User(email=user_data["email"], hashed_password=correct_hashed_password, token="token")
    
    def mock_filter(*args, **kwargs):
        if args[0].right.value == correct_hashed_password: 
            return MagicMock(first=MagicMock(return_value=mock_user))
        return MagicMock(first=MagicMock(return_value=None))
    
    db_session.query().filter = mock_filter

    result = authenticate_user(db_session, user_data["email"], "wrongpassword")  # Неверный пароль

    assert result is None 