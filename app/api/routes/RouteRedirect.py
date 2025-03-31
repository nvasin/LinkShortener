from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import RedirectResponse
from starlette.status import HTTP_404_NOT_FOUND, HTTP_410_GONE
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.DatabaseConnection import SessionLocal
from app.redis.RedisConnection import RedisClient
from app.crud import crud_link
from app.api.ApiDependencies import get_db

router = APIRouter()

@router.get(
    "/{short_code}",
    summary="Редирект по короткой ссылке",
    description="Перенаправляет пользователя на оригинальный URL, связанный с указанным коротким кодом. Если ссылка истекла, возвращается ошибка."
)
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    # 1. Сначала пробуем из кэша
    redis_key = f"short_url:{short_code}"
    original_url = RedisClient.get(redis_key)
    if original_url:
        link = crud_link.get_link_by_short_code(db, short_code)
        crud_link.increment_visit(db, link)
        return RedirectResponse(original_url)

    # 2. Если нет в кэше — ищем в БД
    link = crud_link.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link expired")

    # 3. Кэшируем и редиректим
    RedisClient.set(redis_key, link.original_url)  # Кэшируем ссылку
    crud_link.increment_visit(db, link)
    return RedirectResponse(link.original_url)
