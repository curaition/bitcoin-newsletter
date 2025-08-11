"""Unit tests for the article ingestion pipeline."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from crypto_newsletter.core.ingestion.pipeline import ArticleIngestionPipeline


@pytest.mark.unit
class TestArticleIngestionPipeline:
    """Test cases for ArticleIngestionPipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        return ArticleIngestionPipeline()

    @pytest.fixture
    def mock_coindesk_response(self, sample_coindesk_response):
        """Mock CoinDesk API response."""
        return sample_coindesk_response

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.stats["api_calls"] == 0
        assert pipeline.stats["articles_fetched"] == 0
        assert pipeline.stats["articles_processed"] == 0
        assert pipeline.stats["duplicates_skipped"] == 0
        assert pipeline.stats["errors"] == 0
        assert pipeline.stats["processing_time"] == 0.0

    @pytest.mark.asyncio
    async def test_fetch_articles_from_api(self, pipeline, mock_coindesk_response):
        """Test fetching articles from CoinDesk API."""
        with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_articles.return_value = mock_coindesk_response
            mock_client_class.return_value = mock_client

            articles = await pipeline._fetch_articles_from_api(limit=10)

            assert articles == mock_coindesk_response["Data"]
            assert pipeline.stats["api_calls"] == 1
            assert pipeline.stats["articles_fetched"] == len(mock_coindesk_response["Data"])
            mock_client.fetch_articles.assert_called_once_with(limit=10)

    @pytest.mark.asyncio
    async def test_fetch_articles_api_error(self, pipeline):
        """Test handling API errors during article fetching."""
        with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_articles.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client

            articles = await pipeline._fetch_articles_from_api(limit=10)

            assert articles == []
            assert pipeline.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_filter_recent_articles(self, pipeline, sample_coindesk_response):
        """Test filtering recent articles."""
        articles = sample_coindesk_response["Data"]
        
        # Mock current time to make articles appear recent
        with patch('crypto_newsletter.core.ingestion.pipeline.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.fromtimestamp(1691683300, tz=timezone.utc)
            mock_datetime.fromtimestamp = datetime.fromtimestamp
            
            recent_articles = await pipeline._filter_recent_articles(articles, hours_back=24)

        assert len(recent_articles) <= len(articles)
        assert all(isinstance(article, dict) for article in recent_articles)

    @pytest.mark.asyncio
    async def test_filter_recent_articles_empty_list(self, pipeline):
        """Test filtering with empty article list."""
        recent_articles = await pipeline._filter_recent_articles([], hours_back=24)
        assert recent_articles == []

    @pytest.mark.asyncio
    async def test_process_and_store_articles(self, pipeline, sample_coindesk_response):
        """Test processing and storing articles."""
        articles = sample_coindesk_response["Data"]

        with patch('crypto_newsletter.core.ingestion.pipeline.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            with patch('crypto_newsletter.core.ingestion.pipeline.ArticleProcessor') as mock_processor_class:
                mock_processor = AsyncMock()
                mock_processor.process_articles.return_value = 2
                mock_processor_class.return_value = mock_processor

                processed_count = await pipeline._process_and_store_articles(articles)

                assert processed_count == 2
                mock_processor.process_articles.assert_called_once_with(articles)

    @pytest.mark.asyncio
    async def test_process_and_store_articles_error(self, pipeline, sample_coindesk_response):
        """Test error handling during article processing."""
        articles = sample_coindesk_response["Data"]

        with patch('crypto_newsletter.core.ingestion.pipeline.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.side_effect = Exception("Database error")

            processed_count = await pipeline._process_and_store_articles(articles)

            assert processed_count == 0
            assert pipeline.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_generate_results(self, pipeline):
        """Test generating pipeline results."""
        start_time = datetime.now(timezone.utc)
        pipeline.stats.update({
            "api_calls": 1,
            "articles_fetched": 5,
            "articles_processed": 3,
            "duplicates_skipped": 2,
            "errors": 0
        })

        results = pipeline._generate_results(start_time)

        assert "summary" in results
        assert "processing_time_seconds" in results
        assert "timestamp" in results
        
        summary = results["summary"]
        assert summary["articles_fetched"] == 5
        assert summary["articles_processed"] == 3
        assert summary["duplicates_skipped"] == 2
        assert summary["errors"] == 0
        assert summary["success_rate"] == 0.6  # 3/5

    @pytest.mark.asyncio
    async def test_generate_results_zero_fetched(self, pipeline):
        """Test generating results when no articles fetched."""
        start_time = datetime.now(timezone.utc)
        pipeline.stats.update({
            "api_calls": 1,
            "articles_fetched": 0,
            "articles_processed": 0,
            "duplicates_skipped": 0,
            "errors": 1
        })

        results = pipeline._generate_results(start_time)
        summary = results["summary"]
        assert summary["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_run_full_ingestion_success(self, pipeline, mock_coindesk_response):
        """Test successful full ingestion pipeline."""
        with patch.object(pipeline, '_fetch_articles_from_api', return_value=mock_coindesk_response["Data"]):
            with patch.object(pipeline, '_filter_recent_articles', return_value=mock_coindesk_response["Data"]):
                with patch('crypto_newsletter.core.ingestion.pipeline.deduplicate_articles', return_value=mock_coindesk_response["Data"]):
                    with patch.object(pipeline, '_process_and_store_articles', return_value=2):
                        
                        results = await pipeline.run_full_ingestion(limit=10, hours_back=24)

        assert "summary" in results
        assert "processing_time_seconds" in results
        assert results["summary"]["articles_processed"] == 2

    @pytest.mark.asyncio
    async def test_run_full_ingestion_with_categories(self, pipeline, mock_coindesk_response):
        """Test full ingestion with category filtering."""
        with patch.object(pipeline, '_fetch_articles_from_api', return_value=mock_coindesk_response["Data"]):
            with patch.object(pipeline, '_filter_recent_articles', return_value=mock_coindesk_response["Data"]):
                with patch('crypto_newsletter.core.ingestion.pipeline.deduplicate_articles', return_value=mock_coindesk_response["Data"]):
                    with patch.object(pipeline, '_process_and_store_articles', return_value=1):
                        
                        results = await pipeline.run_full_ingestion(
                            limit=10, 
                            hours_back=24, 
                            categories=["BTC"]
                        )

        assert results["summary"]["articles_processed"] == 1

    @pytest.mark.asyncio
    async def test_health_check_success(self, pipeline):
        """Test successful health check."""
        with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_articles.return_value = {"Data": []}
            mock_client_class.return_value = mock_client

            with patch('crypto_newsletter.core.ingestion.pipeline.get_db_session') as mock_get_session:
                mock_session = AsyncMock()
                mock_get_session.return_value.__aenter__.return_value = mock_session

                health_status = await pipeline.health_check()

        assert health_status["status"] == "healthy"
        assert "checks" in health_status
        assert "coindesk_api" in health_status["checks"]
        assert "database" in health_status["checks"]

    @pytest.mark.asyncio
    async def test_health_check_api_failure(self, pipeline):
        """Test health check with API failure."""
        with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_articles.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client

            with patch('crypto_newsletter.core.ingestion.pipeline.get_db_session') as mock_get_session:
                mock_session = AsyncMock()
                mock_get_session.return_value.__aenter__.return_value = mock_session

                health_status = await pipeline.health_check()

        assert health_status["status"] == "unhealthy"
        assert health_status["checks"]["coindesk_api"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_health_check_database_failure(self, pipeline):
        """Test health check with database failure."""
        with patch('crypto_newsletter.core.ingestion.pipeline.CoinDeskAPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_articles.return_value = {"Data": []}
            mock_client_class.return_value = mock_client

            with patch('crypto_newsletter.core.ingestion.pipeline.get_db_session') as mock_get_session:
                mock_get_session.return_value.__aenter__.side_effect = Exception("Database Error")

                health_status = await pipeline.health_check()

        assert health_status["status"] == "unhealthy"
        assert health_status["checks"]["database"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_reset_stats(self, pipeline):
        """Test resetting pipeline statistics."""
        # Set some stats
        pipeline.stats.update({
            "api_calls": 5,
            "articles_fetched": 10,
            "articles_processed": 8,
            "duplicates_skipped": 2,
            "errors": 1,
            "processing_time": 15.5
        })

        pipeline.reset_stats()

        assert pipeline.stats["api_calls"] == 0
        assert pipeline.stats["articles_fetched"] == 0
        assert pipeline.stats["articles_processed"] == 0
        assert pipeline.stats["duplicates_skipped"] == 0
        assert pipeline.stats["errors"] == 0
        assert pipeline.stats["processing_time"] == 0.0
