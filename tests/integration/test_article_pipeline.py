"""Integration tests for the complete article processing pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from crypto_newsletter.core.ingestion.pipeline import ArticleIngestionPipeline
from crypto_newsletter.core.storage.repository import ArticleRepository
from crypto_newsletter.shared.database.connection import get_db_session


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.coindesk_base_url = "https://data-api.coindesk.com"
    settings.coindesk_api_key = "test-api-key"
    settings.article_retention_hours = 24
    settings.debug = True
    settings.testing = True
    return settings


@pytest.fixture
def sample_coindesk_response():
    """Sample CoinDesk API response for testing."""
    return {
        "Data": [
            {
                "ID": 12345,
                "GUID": "test-guid-1",
                "TITLE": "Bitcoin Reaches New Heights",
                "SUBTITLE": "Market analysis shows positive trends",
                "URL": "https://coindesk.com/test-article-1",
                "BODY": "Bitcoin has reached new heights in today's trading session...",
                "PUBLISHED_ON": 1691683200,  # Recent timestamp
                "AUTHORS": "John Doe",
                "LANG": "EN",
                "KEYWORDS": "bitcoin,cryptocurrency,trading",
                "UPVOTES": 10,
                "DOWNVOTES": 2,
                "SCORE": 8,
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
                    }
                ]
            },
            {
                "ID": 12346,
                "GUID": "test-guid-2", 
                "TITLE": "Ethereum Updates Coming Soon",
                "URL": "https://coindesk.com/test-article-2",
                "BODY": "Ethereum network updates are scheduled...",
                "PUBLISHED_ON": 1691679600,  # Recent timestamp
                "AUTHORS": "Jane Smith",
                "LANG": "EN",
                "SOURCE_DATA": {
                    "ID": 1,
                    "NAME": "CoinDesk",
                    "KEY": "coindesk",
                    "URL": "https://coindesk.com",
                    "LANG": "EN"
                },
                "CATEGORY_DATA": [
                    {
                        "ID": 2,
                        "NAME": "Ethereum",
                        "CATEGORY": "ETH"
                    }
                ]
            }
        ]
    }


@pytest.mark.asyncio
async def test_pipeline_initialization(mock_settings):
    """Test pipeline initialization."""
    pipeline = ArticleIngestionPipeline(settings=mock_settings)
    
    assert pipeline.settings == mock_settings
    assert pipeline.stats["articles_fetched"] == 0
    assert pipeline.stats["articles_processed"] == 0


@pytest.mark.asyncio
async def test_pipeline_health_check(mock_settings):
    """Test pipeline health check functionality."""
    pipeline = ArticleIngestionPipeline(settings=mock_settings)
    
    with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        with patch('crypto_newsletter.core.ingestion.pipeline.get_db_session') as mock_db:
            mock_session = AsyncMock()
            mock_session.execute.return_value.scalar.return_value = 1
            mock_db.return_value.__aenter__.return_value = mock_session
            
            health = await pipeline.health_check()
            
            assert health["status"] == "healthy"
            assert "coindesk_api" in health["checks"]
            assert "database" in health["checks"]
            assert health["checks"]["coindesk_api"]["status"] == "healthy"
            assert health["checks"]["database"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_pipeline_stats_generation(mock_settings):
    """Test pipeline statistics generation."""
    pipeline = ArticleIngestionPipeline(settings=mock_settings)
    
    # Simulate some processing
    pipeline.stats["articles_fetched"] = 10
    pipeline.stats["articles_processed"] = 8
    pipeline.stats["duplicates_skipped"] = 2
    pipeline.stats["errors"] = 0
    
    from datetime import datetime, timezone
    start_time = datetime.now(timezone.utc)
    results = pipeline._generate_results(start_time)
    
    assert results["status"] == "success"
    assert results["statistics"]["articles_fetched"] == 10
    assert results["statistics"]["articles_processed"] == 8
    assert results["summary"]["success_rate"] == 0.8
    assert "processing_time_seconds" in results


@pytest.mark.asyncio 
async def test_pipeline_error_handling(mock_settings):
    """Test pipeline error handling."""
    pipeline = ArticleIngestionPipeline(settings=mock_settings)
    
    with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
        # Simulate API failure
        mock_client_class.return_value.__aenter__.side_effect = Exception("API connection failed")
        
        with pytest.raises(Exception, match="API connection failed"):
            await pipeline.run_full_ingestion()
        
        assert pipeline.stats["errors"] == 1


def test_pipeline_stats_reset(mock_settings):
    """Test pipeline statistics reset."""
    pipeline = ArticleIngestionPipeline(settings=mock_settings)
    
    # Set some stats
    pipeline.stats["articles_fetched"] = 10
    pipeline.stats["errors"] = 1
    
    # Reset
    pipeline.reset_stats()
    
    assert pipeline.stats["articles_fetched"] == 0
    assert pipeline.stats["errors"] == 0
