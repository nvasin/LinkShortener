from fastapi import APIRouter, Depends, HTTPException, Request, Query, Security
from sqlalchemy.orm import Session
from app.database.models.UserModel import User
from app.database.DatabaseConnection import SessionLocal
from app.api.schemas.LinkSchema import LinkCreate, LinkResponse
from app.services.shortener import URLShortener
from app.crud import crud_link
from app.api.ApiDependencies import get_db
from app.api.authentication.UserAuth import get_current_user
from app.database.models.LinkModel import Link
from app.redis.RedisConnection import RedisClient,update_cache
from typing import Optional
import os
from pydantic import BaseModel, AnyHttpUrl, AnyUrl
from datetime import datetime


router = APIRouter()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

class LinkCreate(BaseModel):
    original_url: AnyUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: Optional[AnyUrl]
    expires_at: Optional[datetime]

class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    visit_count: int
    last_visited: Optional[datetime]

# создание короткой ссылки
@router.post(
    "/shorten",
    response_model=LinkResponse,
    summary="Создание короткой ссылки",
    description="Создаёт короткую ссылку для указанного URL. Анонимные пользователи не могут использовать пользовательский алиас."
)
def create_short_link(
    link_in: LinkCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)  # None, если аноним
):
    if not current_user and link_in.custom_alias:
        raise HTTPException(
            status_code=403,
            detail="Custom alias is only available for authenticated users"
        )

    shortener = URLShortener(db)
    try:
        short_code = shortener.create_short_code_or_custom(link_in.custom_alias)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Custom alias already in use"
        )

    user_id = current_user.id if current_user else None  # Если пользователь аноним, user_id = None
    link = crud_link.create_link(db, short_code, link_in, user_id)
    return LinkResponse(
        short_code=short_code,
        short_url=f"{BASE_URL}/{short_code}"
    )


# получение статистики по короткой ссылке
@router.get(
    "/{short_code}/stats",
    response_model=LinkStats,
    summary="Получение статистики по ссылке",
    description="Возвращает статистику для указанной короткой ссылки. Доступно только для авторизованных пользователей."
)
def get_link_stats(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)  # Требуется аутентификация
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    link = crud_link.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Проверяем доступ к статистике
    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    return LinkStats(
        original_url=link.original_url,
        created_at=link.created_at,
        visit_count=link.visit_count,
        last_visited=link.last_visited,
    )


# обновление оригинальной ссылки
@router.put(
    "/{short_code}",
    summary="Обновление короткой ссылки",
    description="Обновляет оригинальный URL или срок действия указанной короткой ссылки. Доступно только для владельца ссылки."
)
def update_link(
    short_code: str,
    link_update: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)  # Требуется аутентификация
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    link = crud_link.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Проверяем, что у ссылки есть владелец и текущий пользователь является владельцем
    if link.user_id is None or link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Обновляем ссылку в базе данных
    updated = crud_link.update_link(db, link, link_update)

    # Удаляем старый кэш
    redis_key = f"short_url:{short_code}"
    RedisClient.delete(redis_key)

    # (Опционально) Обновляем кэш с новым значением
    if link_update.original_url:
        RedisClient.set(redis_key, str(link_update.original_url))

    return {"message": "Link updated successfully"}


# удаление короткой ссылки
@router.delete(
    "/{short_code}",
    summary="Удаление короткой ссылки",
    description="Удаляет указанную короткую ссылку. Доступно только для владельца ссылки."
)
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)  # Требуется аутентификация
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    link = crud_link.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Проверяем, что у ссылки есть владелец и текущий пользователь является владельцем
    if link.user_id is None or link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Удаляем ссылку из базы данных
    crud_link.delete_link(db, link)

    # Удаляем кэш
    update_cache(short_code)

    return {"message": "Link deleted successfully"}

# поиск ссылок
@router.get(
    "/search",
    summary="Поиск ссылок",
    description="Ищет ссылки, принадлежащие текущему пользователю, по указанному оригинальному URL. Доступно только для авторизованных пользователей."
)
def search_links(
    original_url: Optional[str] = Query(None, alias="original_url"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Требуется аутентификация
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    query = db.query(Link).filter(Link.user_id == current_user.id)

    # Если указан параметр original_url, добавляем фильтр
    if original_url:
        query = query.filter(Link.original_url.contains(original_url))

    links = query.all()

    if not links:
        raise HTTPException(status_code=404, detail="No links found")

    return [
        {
            "short_code": link.short_code,
            "short_url": f"{BASE_URL}/{link.short_code}",
            "expires_at": link.expires_at,
        }
        for link in links
    ]


# получение всех коротких ссылок текущего пользователя
@router.get(
    "/my",
    summary="Получение всех ссылок пользователя",
    description="Возвращает все ссылки, принадлежащие текущему пользователю. Доступно только для авторизованных пользователей."
)
def get_my_links(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)  # None, если аноним
):
    if not current_user:
        return []  # Анонимные пользователи не имеют доступных ссылок

    links = db.query(Link).filter(Link.user_id == current_user.id).all()
    return [
        {
            "short_code": link.short_code,
            "short_url": f"{BASE_URL}/{link.short_code}",
            "original_url": link.original_url,
            "expires_at": link.expires_at,
            "created_at": link.created_at,
            "visit_count": link.visit_count,
        }
        for link in links
    ]