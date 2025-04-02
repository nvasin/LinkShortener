import random
import uuid
from datetime import datetime, timedelta
from locust import HttpUser, task, between, constant

AUTH_TOKEN = "00ff1b34-839a-4ce3-a7c7-c6ae0a695d49"

class LinkShortenUser(HttpUser):
    """
    Этот пользователь имитирует обычных пользователей,
    которые массово создают ссылки и запрашивают их.
    """
    wait_time = between(1, 3)
    headers = {"Authorization": AUTH_TOKEN}

    def on_start(self):
        self.created_links = []

    @task(2)
    def create_link(self):
        unique_alias = f"example-{uuid.uuid4().hex[:8]}"
        data = {
            "original_url": "https://google.com",
            "custom_alias": unique_alias,
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"
        }
        with self.client.post("/links/shorten", json=data, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                json_resp = response.json()
                self.created_links.append(json_resp["short_code"])
            else:
                response.failure("Не удалось создать ссылку")

    @task(1)
    def get_link(self):
        # Если ссылки уже созданы, выбираем случайный для GET-запроса
        if self.created_links:
            short_code = random.choice(self.created_links)
            self.client.get(f"/{short_code}", name="/<short_code>")
        else:
            # Если нет ни одной ссылки, создаём одну
            self.create_link()

class CachedLinkUser(HttpUser):
    """
    Этот пользователь создаёт один URL и многократно его запрашивает.
    Это позволяет оценить влияние кэширования на производительность GET-запросов.
    """
    wait_time = constant(1)
    headers = {"Authorization": AUTH_TOKEN}

    def on_start(self):
        unique_alias = f"cached-{uuid.uuid4().hex[:8]}"
        data = {
            "original_url": "https://google.com",
            "custom_alias": unique_alias,
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"
        }
        response = self.client.post("/links/shorten", json=data, headers=self.headers)
        if response.status_code == 200:
            self.short_code = response.json()["short_code"]
        else:
            self.short_code = None

    @task
    def get_cached_link(self):
        if self.short_code:
            self.client.get(f"/{self.short_code}", name="/cached/<short_code>")
