from sqlalchemy.orm import Session
from app.database.models.UserModel import User
from app.api.schemas.UserSchema import UserCreate
from typing import Optional
import hashlib
import uuid

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = hashlib.sha256(user_in.password.encode()).hexdigest()  # Хэшируем пароль
    token = str(uuid.uuid4())  # Генерируем уникальный токен
    db_user = User(email=user_in.email, hashed_password=hashed_password, token=token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return db.query(User).filter(User.email == email, User.hashed_password == hashed_password).first()