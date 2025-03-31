from pydantic import BaseModel, AnyHttpUrl
from typing import Optional
from datetime import datetime

# ----- Запрос на создание короткой ссылки -----
class LinkCreate(BaseModel):
    original_url: AnyHttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

# ----- Ответ при создании -----
class LinkResponse(BaseModel):
    short_code: str
    short_url: str

    class Config:
        from_attributes = True

# ----- Статистика по ссылке -----
class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    visit_count: int
    last_visited: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

# ----- Обновление ссылки -----
class LinkUpdate(BaseModel):
    original_url: Optional[AnyHttpUrl]
    expires_at: Optional[datetime]