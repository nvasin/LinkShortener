from fastapi import FastAPI
from app.api.routes import RouteAuth, RouteLinks, RouteRedirect
from app.database.DatabaseInitializer import init_db
from dotenv import load_dotenv
import os

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.database.DatabaseConnection import SessionLocal
from app.database.models.LinkModel import Link

# Загружаем переменные окружения из .env
load_dotenv()

# Получаем переменные окружения
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
BASE_URL = os.getenv("BASE_URL")

app = FastAPI(title="URL Shortener Service")

app.include_router(RouteAuth.router, prefix="/auth")
app.include_router(RouteLinks.router, prefix="/links")
app.include_router(RouteRedirect.router)


def delete_old_links():
    """
    Удаляет ссылки, которые не использовались более 14 дней.
    """
    db = SessionLocal()
    try:
        threshold_date = datetime.utcnow() - timedelta(days=14)
        old_links = db.query(Link).filter(Link.last_visited < threshold_date).all()

        for link in old_links:
            print(f"Удаление ссылки: {link.short_code} -> {link.original_url}")
            db.delete(link)

        db.commit()
    except Exception as e:
        print(f"Ошибка при удалении старых ссылок: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_links, "interval", minutes=60)
scheduler.start()



@app.on_event("startup")
def startup():
    init_db()

