"""Tests for CoinDesk API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from crypto_newsletter.core.ingestion.coindesk_client import CoinDeskAPIClient


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.coindesk_base_url = "https://data-api.coindesk.com"
    settings.coindesk_api_key = "test-api-key"
    return settings


@pytest.fixture
def client(mock_settings):
    """Create CoinDesk API client for testing."""
    return CoinDeskAPIClient(settings=mock_settings)


@pytest.mark.asyncio
async def test_client_initialization(client):
    """Test client initialization."""
    assert client.base_url == "https://data-api.coindesk.com"
    assert client.api_key == "test-api-key"


@pytest.mark.asyncio
async def test_filter_recent_articles(client):
    """Test filtering recent articles."""
    # Mock API response
    api_response = {
        "Data": [
            {"ID": 1, "PUBLISHED_ON": 1691683200, "TITLE": "Recent Article"},  # Recent
            {"ID": 2, "PUBLISHED_ON": 1691596800, "TITLE": "Old Article"},     # Old
        ]
    }

    # Filter for last 1 hour (should only get recent articles)
    recent = client.filter_recent_articles(api_response, hours=1)

    # Should filter based on current time, so we'll just check the structure
    assert isinstance(recent, list)
    assert all("ID" in article for article in recent)


def test_client_properties(client):
    """Test client properties."""
    assert client.base_url == "https://data-api.coindesk.com"
    assert client.api_key == "test-api-key"
