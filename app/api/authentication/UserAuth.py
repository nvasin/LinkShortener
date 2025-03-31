from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.models.UserModel import User
from app.api.ApiDependencies import get_db
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def create_access_token(user_id: int) -> str:
    payload = {"sub": user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User | None:
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        return None  # Возвращаем None, если заголовок отсутствует

    # Проверяем токен в базе данных
    user = db.query(User).filter(User.token == authorization).first()
    if not user:
        raise HTTPException(status_code=403, detail="Invalid token")
    return user