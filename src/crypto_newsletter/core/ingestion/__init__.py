"""CoinDesk API ingestion module."""

from .article_processor import ArticleProcessor
from .coindesk_client import CoinDeskAPIClient, fetch_coindesk_articles
from .deduplication import ArticleDeduplicator, deduplicate_articles

__all__ = [
    "CoinDeskAPIClient",
    "ArticleProcessor",
    "ArticleDeduplicator",
    "fetch_coindesk_articles",
    "deduplicate_articles",
]