"""Batch processing configuration and settings."""

from dataclasses import dataclass
from typing import Any


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing operations."""

    # Batch sizing
    BATCH_SIZE: int = 10  # Articles per batch
    MAX_TOTAL_BUDGET: float = 0.30  # USD
    ESTIMATED_COST_PER_ARTICLE: float = 0.0013  # USD

    # Timing and delays
    MAX_RETRY_ATTEMPTS: int = 3
    PROCESSING_TIMEOUT: int = 300  # 5 minutes per article
    BATCH_DELAY: int = 30  # Seconds between batches

    # Cost monitoring thresholds
    COST_WARNING_THRESHOLD: float = 0.20  # 67% of budget
    COST_CRITICAL_THRESHOLD: float = 0.25  # 83% of budget

    # Quality thresholds
    MIN_CONTENT_LENGTH: int = 1000  # Minimum article length
    MIN_ARTICLES_FOR_BATCH: int = 3  # Minimum articles needed to start batch

    # Processing limits
    MAX_ARTICLES_PER_SESSION: int = 200  # Safety limit
    MAX_CONCURRENT_BATCHES: int = 2  # Prevent system overload

    @classmethod
    def get_estimated_total_cost(cls, article_count: int) -> float:
        """Calculate estimated total cost for processing articles."""
        return article_count * cls.ESTIMATED_COST_PER_ARTICLE

    @classmethod
    def get_batch_count(cls, article_count: int) -> int:
        """Calculate number of batches needed for article count."""
        return (article_count + cls.BATCH_SIZE - 1) // cls.BATCH_SIZE

    @classmethod
    def validate_budget(cls, article_count: int) -> dict[str, Any]:
        """Validate if article count fits within budget constraints."""
        estimated_cost = cls.get_estimated_total_cost(article_count)

        return {
            "article_count": article_count,
            "estimated_cost": estimated_cost,
            "max_budget": cls.MAX_TOTAL_BUDGET,
            "within_budget": estimated_cost <= cls.MAX_TOTAL_BUDGET,
            "budget_utilization": (estimated_cost / cls.MAX_TOTAL_BUDGET) * 100,
            "cost_per_article": cls.ESTIMATED_COST_PER_ARTICLE,
        }

    @classmethod
    def get_processing_timeline(cls, article_count: int) -> dict[str, Any]:
        """Calculate estimated processing timeline."""
        batch_count = cls.get_batch_count(article_count)

        # Estimate processing time per batch (including delays)
        time_per_batch = (
            cls.BATCH_SIZE * 30
        ) + cls.BATCH_DELAY  # 30 seconds per article + delay
        total_time_seconds = batch_count * time_per_batch

        return {
            "article_count": article_count,
            "batch_count": batch_count,
            "articles_per_batch": cls.BATCH_SIZE,
            "estimated_time_seconds": total_time_seconds,
            "estimated_time_minutes": total_time_seconds / 60,
            "estimated_time_hours": total_time_seconds / 3600,
        }


# Global configuration instance
batch_config = BatchProcessingConfig()
