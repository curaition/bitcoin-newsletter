"""Integrated article processing pipeline orchestrator."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session

from .article_processor import ArticleProcessor
from .coindesk_client import CoinDeskAPIClient
from .deduplication import deduplicate_articles


class ArticleIngestionPipeline:
    """Orchestrates the complete article ingestion and processing pipeline."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        """Initialize the pipeline with optional settings override."""
        self.settings = settings or get_settings()
        self.stats = {
            "api_calls": 0,
            "articles_fetched": 0,
            "articles_processed": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "processing_time": 0.0,
        }

    async def run_full_ingestion(
        self,
        limit: int = 50,
        hours_back: int = 24,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run the complete article ingestion pipeline.

        Args:
            limit: Maximum number of articles to fetch from API
            hours_back: Filter articles from last N hours
            categories: Categories to filter by (default: ["BTC"])

        Returns:
            Dictionary with processing statistics and results
        """
        start_time = datetime.now(timezone.utc)
        logger.info(
            f"Starting article ingestion pipeline - "
            f"limit: {limit}, hours_back: {hours_back}, categories: {categories}"
        )

        try:
            # Step 1: Fetch articles from CoinDesk API
            articles_data = await self._fetch_articles(limit, categories)
            self.stats["api_calls"] += 1
            self.stats["articles_fetched"] = len(articles_data)

            if not articles_data:
                logger.warning("No articles fetched from CoinDesk API")
                return self._generate_results(start_time)

            # Step 2: Filter recent articles
            recent_articles = await self._filter_recent_articles(articles_data, hours_back)
            logger.info(f"Filtered to {len(recent_articles)} recent articles")

            # Step 3: In-memory deduplication
            unique_articles = deduplicate_articles(recent_articles)
            logger.info(f"After deduplication: {len(unique_articles)} unique articles")

            # Step 4: Process and store articles
            processed_count = await self._process_and_store_articles(unique_articles)
            self.stats["articles_processed"] = processed_count
            self.stats["duplicates_skipped"] = len(recent_articles) - len(unique_articles)

            # Step 5: Generate final results
            return self._generate_results(start_time)

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Pipeline execution failed: {e}")
            raise

    async def _fetch_articles(
        self, limit: int, categories: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Fetch articles from CoinDesk API."""
        logger.debug("Fetching articles from CoinDesk API")

        async with CoinDeskAPIClient(self.settings) as client:
            # Fetch articles directly (connection test is implicit)
            api_response = await client.get_latest_articles(
                limit=limit, categories=categories
            )

            articles = api_response.get("Data", [])
            logger.info(f"Successfully fetched {len(articles)} articles from CoinDesk API")

            return articles

    async def _filter_recent_articles(
        self, articles: List[Dict[str, Any]], hours_back: int
    ) -> List[Dict[str, Any]]:
        """Filter articles to recent time window."""
        logger.debug(f"Filtering articles for last {hours_back} hours")

        # Use the client's filtering method
        client = CoinDeskAPIClient(self.settings)
        # Create a mock response to use the filter method
        mock_response = {"Data": articles}
        recent_articles = client.filter_recent_articles(
            mock_response, hours=hours_back
        )

        logger.info(f"Filtered to {len(recent_articles)} recent articles")
        return recent_articles

    async def _process_and_store_articles(
        self, articles: List[Dict[str, Any]]
    ) -> int:
        """Process and store articles in database."""
        logger.debug(f"Processing and storing {len(articles)} articles")

        async with get_db_session() as db_session:
            processor = ArticleProcessor(db_session)
            processed_count = await processor.process_articles(articles)

        logger.info(f"Successfully processed and stored {processed_count} articles")
        return processed_count

    def _generate_results(self, start_time: datetime) -> Dict[str, Any]:
        """Generate pipeline execution results."""
        end_time = datetime.now(timezone.utc)
        self.stats["processing_time"] = (end_time - start_time).total_seconds()

        results = {
            "status": "success" if self.stats["errors"] == 0 else "partial_success",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "processing_time_seconds": self.stats["processing_time"],
            "statistics": self.stats.copy(),
            "summary": {
                "articles_fetched": self.stats["articles_fetched"],
                "articles_processed": self.stats["articles_processed"],
                "duplicates_skipped": self.stats["duplicates_skipped"],
                "success_rate": (
                    self.stats["articles_processed"] / self.stats["articles_fetched"]
                    if self.stats["articles_fetched"] > 0
                    else 0
                ),
                "errors": self.stats["errors"],
            },
        }

        logger.info(f"Pipeline completed: {results['summary']}")
        return results

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of all pipeline components."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
        }

        # Check CoinDesk API
        try:
            async with CoinDeskAPIClient(self.settings) as client:
                api_healthy = await client.test_connection()
                health_status["checks"]["coindesk_api"] = {
                    "status": "healthy" if api_healthy else "unhealthy",
                    "message": "API connection successful" if api_healthy else "API connection failed",
                }
        except Exception as e:
            health_status["checks"]["coindesk_api"] = {
                "status": "unhealthy",
                "message": f"API check failed: {e}",
            }

        # Check database
        try:
            async with get_db_session() as db_session:
                # Simple query to test database
                from sqlalchemy import text
                result = await db_session.execute(text("SELECT 1"))
                db_healthy = result.scalar() == 1
                health_status["checks"]["database"] = {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "message": "Database connection successful" if db_healthy else "Database query failed",
                }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "message": f"Database check failed: {e}",
            }

        # Determine overall status
        if any(
            check["status"] == "unhealthy"
            for check in health_status["checks"].values()
        ):
            health_status["status"] = "unhealthy"

        return health_status

    def reset_stats(self) -> None:
        """Reset pipeline statistics."""
        self.stats = {
            "api_calls": 0,
            "articles_fetched": 0,
            "articles_processed": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "processing_time": 0.0,
        }


# Convenience functions for external use
async def run_article_ingestion(
    limit: int = 50,
    hours_back: int = 24,
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run article ingestion pipeline.

    Args:
        limit: Maximum number of articles to fetch
        hours_back: Filter articles from last N hours  
        categories: Categories to filter by

    Returns:
        Pipeline execution results
    """
    pipeline = ArticleIngestionPipeline()
    return await pipeline.run_full_ingestion(limit, hours_back, categories)


async def pipeline_health_check() -> Dict[str, Any]:
    """
    Convenience function for pipeline health check.

    Returns:
        Health check results
    """
    pipeline = ArticleIngestionPipeline()
    return await pipeline.health_check()


async def quick_ingestion_test() -> bool:
    """
    Quick test to verify pipeline is working.

    Returns:
        True if pipeline test successful, False otherwise
    """
    try:
        pipeline = ArticleIngestionPipeline()
        results = await pipeline.run_full_ingestion(limit=5, hours_back=24)
        return results["status"] in ["success", "partial_success"]
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        return False
