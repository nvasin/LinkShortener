import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime, timedelta
import uuid

client = TestClient(app, follow_redirects=False)
AUTH_TOKEN = "00ff1b34-839a-4ce3-a7c7-c6ae0a695d49"

@pytest.fixture
def test_data_with_alias():
    unique_alias = f"example-{uuid.uuid4().hex[:8]}"
    return {
        "original_url": "https://google.com",
        "custom_alias": unique_alias,
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"
    }

@pytest.fixture
def test_data_random():
    return {
        "original_url": "https://google.com",
        "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"
    }

@pytest.fixture
def created_link(test_data_with_alias):
    headers = {"Authorization": AUTH_TOKEN}
    response = client.post("/links/shorten", json=test_data_with_alias, headers=headers)
    assert response.status_code == 200
    return response.json(), test_data_with_alias

def test_create_link_with_custom_alias(test_data_with_alias):
    headers = {"Authorization": AUTH_TOKEN}
    response = client.post("/links/shorten", json=test_data_with_alias, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == test_data_with_alias["custom_alias"]
    assert data["short_url"] == f"http://localhost:8000/{test_data_with_alias['custom_alias']}"

def test_create_link_with_random_code(test_data_random):
    headers = {"Authorization": AUTH_TOKEN}
    response = client.post("/links/shorten", json=test_data_random, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "short_code" in data
    assert data["short_code"] != ""
    assert data["short_code"] != test_data_random.get("custom_alias", "")
    assert data["short_url"].startswith("http://localhost:8000/")

def test_get_link_by_short_code(created_link):
    link_data, original_request = created_link
    short_code = link_data["short_code"]
    response = client.get(f"/{short_code}")

    print(f"DEBUG: GET /{short_code}")
    print("DEBUG: Response status code:", response.status_code)
    print("DEBUG: Response headers:", response.headers)
    print("DEBUG: Expected location:", original_request["original_url"])
    assert response.status_code == 307, f"Expected status 307, got {response.status_code}"


def test_create_link_with_invalid_data():
    headers = {"Authorization": AUTH_TOKEN}
    response = client.post("/links/shorten", json={"custom_alias": "invalid"}, headers=headers)
    assert response.status_code == 422

def test_redirect_invalid_short_code():
    response = client.get("/invalid_code")
    assert response.status_code == 404
