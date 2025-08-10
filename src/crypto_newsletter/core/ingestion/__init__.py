"""CoinDesk API ingestion module."""

from .article_processor import ArticleProcessor
from .coindesk_client import CoinDeskAPIClient, fetch_coindesk_articles
from .deduplication import ArticleDeduplicator, deduplicate_articles
from .pipeline import (
    ArticleIngestionPipeline,
    pipeline_health_check,
    quick_ingestion_test,
    run_article_ingestion,
)

__all__ = [
    "CoinDeskAPIClient",
    "ArticleProcessor",
    "ArticleDeduplicator",
    "ArticleIngestionPipeline",
    "fetch_coindesk_articles",
    "deduplicate_articles",
    "run_article_ingestion",
    "pipeline_health_check",
    "quick_ingestion_test",
]