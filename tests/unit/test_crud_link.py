import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database.models.LinkModel import Link
from app.api.schemas.LinkSchema import LinkCreate, LinkUpdate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.BaseModel import Base
from app.database.models.LinkModel import Link
from app.database.models.UserModel import User

from app.crud.crud_link import (
    create_link,
    get_link_by_short_code,
    get_link_by_custom_alias,
    get_link_by_original_url,
    update_link,
    delete_link,
    increment_visit,
)

@pytest.fixture
def db_session():

    engine = create_engine("sqlite:///:memory:")  # SQLite в памяти для тестов
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


@pytest.fixture
def link_data():
    return LinkCreate(
        original_url="https://example.com",
        custom_alias="example",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

def test_create_link(db_session: Session, link_data: LinkCreate):
    short_code = "abc123"
    user_id = 1
    link = create_link(db_session, short_code, link_data, user_id)
    assert link.short_code == short_code
    assert link.original_url == str(link_data.original_url)
    assert link.custom_alias == link_data.custom_alias
    assert link.user_id == user_id

def test_get_link_by_short_code(db_session: Session, link_data: LinkCreate):
    short_code = "abc123"
    link = create_link(db_session, short_code, link_data)
    fetched_link = get_link_by_short_code(db_session, short_code)
    assert fetched_link is not None
    assert fetched_link.short_code == short_code

def test_get_link_by_custom_alias(db_session: Session, link_data: LinkCreate):
    short_code = "abc123"
    link = create_link(db_session, short_code, link_data)
    fetched_link = get_link_by_custom_alias(db_session, link_data.custom_alias)
    assert fetched_link is not None
    assert fetched_link.custom_alias == link_data.custom_alias

def test_update_link(db_session: Session, link_data: LinkCreate):
    short_code = "abc123"
    link = create_link(db_session, short_code, link_data)
    update_data = LinkUpdate(
        original_url="https://updated.com",
        expires_at=(datetime.now(timezone.utc) + timedelta(days=2)).replace(tzinfo=None),
    )
    updated_link = update_link(db_session, link, update_data)
    assert updated_link.original_url == str(update_data.original_url)
    assert updated_link.expires_at == update_data.expires_at


def test_delete_link(db_session: Session, link_data: LinkCreate):
    short_code = "abc123"
    link = create_link(db_session, short_code, link_data)
    delete_link(db_session, link)
    fetched_link = get_link_by_short_code(db_session, short_code)
    assert fetched_link is None

def test_increment_visit(db_session: Session, link_data: LinkCreate):
    short_code = "abc123"
    link = create_link(db_session, short_code, link_data)
    initial_visit_count = link.visit_count
    increment_visit(db_session, link)
    assert link.visit_count == initial_visit_count + 1
    assert link.last_visited is not None