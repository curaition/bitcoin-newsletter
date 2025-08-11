"""Shared pytest fixtures and configuration for the crypto newsletter test suite."""

import asyncio
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from crypto_newsletter.shared.config.settings import Settings
from crypto_newsletter.shared.database.connection import DatabaseManager
from crypto_newsletter.shared.models import Base
from crypto_newsletter.web.main import create_app


# Configure pytest-asyncio
pytest_asyncio.fixture(scope="session")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return MagicMock(spec=Settings, **{
        'database_url': 'sqlite+aiosqlite:///:memory:',
        'redis_url': 'redis://localhost:6379/1',
        'coindesk_api_key': 'test-api-key',
        'coindesk_base_url': 'https://data-api.coindesk.com',
        'debug': True,
        'testing': True,
        'enable_celery': False,
        'railway_environment': 'testing',
        'service_type': 'web',
        'article_retention_hours': 24,
        'log_level': 'DEBUG',
    })


@pytest.fixture
async def test_db_engine():
    """Create a test database engine with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    return {
        "ID": 12345,
        "GUID": "test-guid-12345",
        "TITLE": "Bitcoin Reaches New All-Time High",
        "SUBTITLE": "Market analysis shows bullish trends",
        "URL": "https://coindesk.com/test-article-12345",
        "BODY": "Bitcoin has reached a new all-time high in today's trading session, driven by institutional adoption and positive market sentiment. The cryptocurrency broke through the $50,000 barrier for the first time, marking a significant milestone in its price history.",
        "PUBLISHED_ON": int(datetime.now(timezone.utc).timestamp()),
        "PUBLISHED_ON_NS": int(datetime.now(timezone.utc).timestamp() * 1_000_000_000),
        "AUTHORS": "John Doe, Jane Smith",
        "LANG": "EN",
        "KEYWORDS": "bitcoin,cryptocurrency,trading,all-time-high",
        "IMAGE_URL": "https://coindesk.com/images/test-image.jpg",
        "UPVOTES": 15,
        "DOWNVOTES": 3,
        "SCORE": 12,
        "SENTIMENT": "POSITIVE",
        "SOURCE_DATA": {
            "ID": 1,
            "NAME": "CoinDesk",
            "KEY": "coindesk",
            "URL": "https://coindesk.com",
            "LANG": "EN"
        },
        "CATEGORY_DATA": [
            {
                "ID": 1,
                "NAME": "Bitcoin",
                "CATEGORY": "BTC"
            },
            {
                "ID": 5,
                "NAME": "Trading",
                "CATEGORY": "TRADING"
            }
        ]
    }


@pytest.fixture
def sample_coindesk_response(sample_article_data):
    """Sample CoinDesk API response for testing."""
    return {
        "Data": [
            sample_article_data,
            {
                **sample_article_data,
                "ID": 12346,
                "GUID": "test-guid-12346",
                "TITLE": "Ethereum Network Upgrade Scheduled",
                "URL": "https://coindesk.com/test-article-12346",
                "CATEGORY_DATA": [
                    {
                        "ID": 2,
                        "NAME": "Ethereum",
                        "CATEGORY": "ETH"
                    }
                ]
            }
        ],
        "Message": "Success",
        "Type": 100
    }


@pytest.fixture
def mock_coindesk_client():
    """Mock CoinDesk API client for testing."""
    client = AsyncMock()
    client.fetch_articles = AsyncMock()
    client.filter_recent_articles = MagicMock()
    return client


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.flushdb.return_value = True
    return redis_mock


@pytest.fixture
def test_client(mock_settings):
    """Create a test client for FastAPI application."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up test environment
        os.environ["TESTING"] = "true"
        os.environ["DATABASE_URL"] = "sqlite:///test.db"
        
        app = create_app()
        
        with TestClient(app) as client:
            yield client


@pytest.fixture
def sample_publisher_data():
    """Sample publisher data for testing."""
    return {
        "ID": 1,
        "NAME": "CoinDesk",
        "KEY": "coindesk",
        "URL": "https://coindesk.com",
        "LANG": "EN"
    }


@pytest.fixture
def sample_category_data():
    """Sample category data for testing."""
    return [
        {
            "ID": 1,
            "NAME": "Bitcoin",
            "CATEGORY": "BTC"
        },
        {
            "ID": 2,
            "NAME": "Ethereum", 
            "CATEGORY": "ETH"
        },
        {
            "ID": 3,
            "NAME": "Trading",
            "CATEGORY": "TRADING"
        }
    ]


@pytest.fixture
def mock_celery_app():
    """Mock Celery application for testing."""
    celery_mock = MagicMock()
    celery_mock.send_task = MagicMock()
    celery_mock.control.inspect.return_value.active.return_value = {}
    celery_mock.control.inspect.return_value.scheduled.return_value = {}
    celery_mock.control.inspect.return_value.reserved.return_value = {}
    return celery_mock


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        yield f.name
    
    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_article_data(
        article_id: int = 12345,
        title: str = "Test Article",
        url: str = "https://example.com/test",
        **kwargs
    ) -> Dict[str, Any]:
        """Create article data for testing."""
        base_data = {
            "ID": article_id,
            "GUID": f"test-guid-{article_id}",
            "TITLE": title,
            "URL": url,
            "BODY": "Test article body content",
            "PUBLISHED_ON": int(datetime.now(timezone.utc).timestamp()),
            "AUTHORS": "Test Author",
            "LANG": "EN",
            "SOURCE_DATA": {
                "ID": 1,
                "NAME": "Test Publisher",
                "KEY": "test",
                "URL": "https://test.com",
                "LANG": "EN"
            },
            "CATEGORY_DATA": [
                {
                    "ID": 1,
                    "NAME": "Bitcoin",
                    "CATEGORY": "BTC"
                }
            ]
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_multiple_articles(count: int = 3) -> List[Dict[str, Any]]:
        """Create multiple articles for testing."""
        return [
            TestDataFactory.create_article_data(
                article_id=12345 + i,
                title=f"Test Article {i + 1}",
                url=f"https://example.com/test-{i + 1}"
            )
            for i in range(count)
        ]


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory


# Async test helpers
@pytest.fixture
async def async_mock():
    """Create an AsyncMock for testing."""
    return AsyncMock()


# Markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
