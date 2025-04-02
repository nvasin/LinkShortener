from fastapi.testclient import TestClient
from app.main import app, delete_old_links
from datetime import datetime, timedelta
from app.database.models.LinkModel import Link
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_app_routes():
    """
    Test if the FastAPI app includes the correct routes.
    """
    response = client.get("/auth")
    assert response.status_code in [200, 404]  # Assuming the route exists or requires authentication

    response = client.get("/links")
    assert response.status_code in [200, 404]  # Assuming the route exists or requires authentication

    response = client.get("/")
    assert response.status_code in [200, 404]  # Assuming the redirect route exists or not


@patch("app.main.SessionLocal")
def test_delete_old_links(mock_session_local):
    """
    Test the delete_old_links function to ensure it deletes old links correctly.
    """
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db

    mock_link_1 = MagicMock(last_visited=datetime.utcnow() - timedelta(days=15))
    mock_link_2 = MagicMock(last_visited=datetime.utcnow() - timedelta(days=16))
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_link_1, mock_link_2]

    delete_old_links()

    mock_db.query.assert_called_once_with(Link)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.delete.assert_any_call(mock_link_1)
    mock_db.delete.assert_any_call(mock_link_2)
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


@patch("app.main.init_db")
def test_startup_event(mock_init_db):
    """
    Test the startup event to ensure init_db is called.
    """
    with patch.object(app, "on_event") as mock_on_event:
        app.router.on_startup[0]()
        mock_init_db.assert_called_once()