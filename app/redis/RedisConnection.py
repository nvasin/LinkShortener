import os
import redis
from typing import Optional 
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройка подключения к Redis
RedisClient = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

def update_cache(short_code: str, original_url: Optional[str] = None):
    """
    Обновляет или удаляет кэш для указанного короткого кода.
    
    :param short_code: Короткий код ссылки.
    :param original_url: Новый оригинальный URL. Если None, ключ будет удалён.
    """
    redis_key = f"short_url:{short_code}"
    try:
        if original_url:
            # Обновляем кэш
            RedisClient.set(redis_key, original_url)
        else:
            # Удаляем кэш
            RedisClient.delete(redis_key)
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Ошибка при работе с Redis: {e}")