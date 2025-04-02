import pytest
from unittest.mock import MagicMock, patch
from app.services.shortener import URLShortener

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def url_shortener(mock_db):
    return URLShortener(db=mock_db)

@patch("app.services.shortener.crud_link.get_link_by_short_code")
def test_generate_short_code(mock_get_link_by_short_code, url_shortener):
    mock_get_link_by_short_code.return_value = None  # Симулируем, что код уникален

    short_code = url_shortener.generate_short_code()

    assert len(short_code) == 6
    assert short_code.isalnum()
    mock_get_link_by_short_code.assert_called()

@patch("app.services.shortener.crud_link.get_link_by_custom_alias")
def test_create_short_code_or_custom_with_custom_alias(mock_get_link_by_custom_alias, url_shortener):
    custom_alias = "custom123"
    mock_get_link_by_custom_alias.return_value = None  # Симулируем, что алиас уникален

    result = url_shortener.create_short_code_or_custom(custom_alias)

    assert result == custom_alias
    mock_get_link_by_custom_alias.assert_called_with(url_shortener.db, custom_alias)

@patch("app.services.shortener.crud_link.get_link_by_custom_alias")
def test_create_short_code_or_custom_with_existing_custom_alias(mock_get_link_by_custom_alias, url_shortener):
    custom_alias = "custom123"
    mock_get_link_by_custom_alias.return_value = True  # Симулируем, что алиас уже существует

    with pytest.raises(ValueError, match="Alias already in use"):
        url_shortener.create_short_code_or_custom(custom_alias)

    mock_get_link_by_custom_alias.assert_called_with(url_shortener.db, custom_alias)

@patch("app.services.shortener.crud_link.get_link_by_short_code")
def test_create_short_code_or_custom_without_custom_alias(mock_get_link_by_short_code, url_shortener):
    mock_get_link_by_short_code.return_value = None  # Симулируем, что код уникален

    result = url_shortener.create_short_code_or_custom(None)

    assert len(result) == 6
    assert result.isalnum()
    mock_get_link_by_short_code.assert_called()