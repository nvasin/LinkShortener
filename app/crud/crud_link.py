from sqlalchemy.orm import Session
from datetime import datetime
from app.database.models.LinkModel import Link
from app.api.schemas.LinkSchema import LinkCreate, LinkUpdate
from typing import Optional

# Создает новую запись в таблице Link с указанным коротким кодом и данными ссылки.
# Если user_id указан, то ссылка будет связана с пользователем.
def create_link(db: Session, short_code: str, link: LinkCreate, user_id: Optional[int] = None) -> Link:
    db_link = Link(
        original_url=str(link.original_url),  # Преобразуем AnyUrl в строку
        short_code=short_code,
        custom_alias=link.custom_alias,
        expires_at=link.expires_at,
        user_id=user_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

# Ищет ссылку по короткому коду.
# Возвращает объект Link или None, если запись не найдена.
def get_link_by_short_code(db: Session, short_code: str) -> Optional[Link]:
    return db.query(Link).filter(Link.short_code == short_code).first()

# Ищет ссылку по пользовательскому алиасу.
# Возвращает объект Link или None, если запись не найдена.
def get_link_by_custom_alias(db: Session, alias: str) -> Optional[Link]:
    return db.query(Link).filter(Link.custom_alias == alias).first()

# Ищет ссылку по оригинальному URL.
# Возвращает объект Link или None, если запись не найдена.
def get_link_by_original_url(db: Session, url: str) -> Optional[Link]:
    return db.query(Link).filter(Link.original_url == url).first()

# Обновляет существующую запись в таблице Link.
# Обновляет поля original_url и expires_at, если они указаны.
# Возвращает обновленный объект Link.
def update_link(db: Session, db_link: Link, link_update: LinkUpdate) -> Link:
    if link_update.original_url:
        # Преобразуем AnyUrl в строку
        db_link.original_url = str(link_update.original_url)
    if link_update.expires_at:
        db_link.expires_at = link_update.expires_at
    db.commit()
    db.refresh(db_link)
    return db_link

# Удаляет запись из таблицы Link.
# Не возвращает значения.
def delete_link(db: Session, db_link: Link) -> None:
    db.delete(db_link)
    db.commit()

# Увеличивает счетчик посещений ссылки.
# Обновляет поле last_visited текущей датой и временем.
# Не возвращает значения.
def increment_visit(db: Session, db_link: Link) -> None:
    db_link.visit_count += 1
    db_link.last_visited = datetime.utcnow()
    db.commit()
