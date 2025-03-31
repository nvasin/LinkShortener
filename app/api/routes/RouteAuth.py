from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.UserSchema import UserCreate, UserResponse
from app.crud import crud_user
from app.api.ApiDependencies import get_db
from app.api.authentication.UserAuth import create_access_token

router = APIRouter()

# регистрация нового пользователя
@router.post(
    "/register",
    response_model=UserResponse,
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя с указанным email и паролем. Если email уже зарегистрирован, возвращается ошибка."
)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = crud_user.get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud_user.create_user(db, user_in)
    return user

# вход пользователя
@router.post(
    "/login",
    response_model=UserResponse,
    summary="Вход пользователя",
    description="Авторизует пользователя с указанным email и паролем. Возвращает информацию о пользователе, если данные корректны."
)
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = crud_user.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    return user