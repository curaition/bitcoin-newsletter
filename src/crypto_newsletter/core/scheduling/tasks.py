"""Celery tasks for scheduled operations."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from celery import Task
from loguru import logger

from crypto_newsletter.core.ingestion.pipeline import ArticleIngestionPipeline
from crypto_newsletter.core.ingestion import pipeline_health_check
from crypto_newsletter.core.storage.repository import ArticleRepository
from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.celery.health import check_celery_health
from crypto_newsletter.shared.database.connection import get_db_session


class AsyncTask(Task):
    """Base task class for async operations."""

    def __call__(self, *args, **kwargs):
        """Execute async task in event loop."""
        # Remove self from args since it's already bound
        return asyncio.run(self.run_async(*args, **kwargs))

    async def run_async(self, *args, **kwargs):
        """Override this method in subclasses."""
        raise NotImplementedError


@celery_app.task(
    bind=True,
    name="crypto_newsletter.core.scheduling.tasks.ingest_articles",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def ingest_articles(
    self,
    limit: Optional[int] = None,
    hours_back: int = 4,
    categories: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Scheduled task to ingest articles from CoinDesk API.
    
    Args:
        limit: Maximum number of articles to fetch (None for no limit)
        hours_back: How many hours back to look for articles
        categories: List of categories to filter by (None for all)
    
    Returns:
        Dict with ingestion results and metrics
    """
    async def _run_ingestion():
        task_start = datetime.now(timezone.utc)

        try:
            logger.info(
                f"Starting scheduled article ingestion - "
                f"limit: {limit}, hours_back: {hours_back}, categories: {categories}"
            )

            # Run the ingestion pipeline
            pipeline = ArticleIngestionPipeline()
            results = await pipeline.run_full_ingestion(
                limit=limit,
                hours_back=hours_back,
                categories=categories,
            )

            # Calculate processing time
            processing_time = (datetime.now(timezone.utc) - task_start).total_seconds()
            results["processing_time_seconds"] = processing_time
            results["task_completed_at"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                f"Scheduled ingestion completed successfully - "
                f"processed: {results.get('articles_processed', 0)}, "
                f"time: {processing_time:.2f}s"
            )

            return results

        except Exception as exc:
            logger.error(f"Scheduled ingestion failed: {exc}")

            # Retry logic with exponential backoff
            if self.request.retries < self.max_retries:
                retry_delay = min(300 * (2 ** self.request.retries), 1800)  # Max 30 min
                logger.warning(
                    f"Retrying ingestion in {retry_delay} seconds "
                    f"(attempt {self.request.retries + 1}/{self.max_retries})"
                )
                raise self.retry(countdown=retry_delay, exc=exc)

            # Final failure
            logger.error(f"Ingestion failed after {self.max_retries} retries")
            return {
                "success": False,
                "error": str(exc),
                "task_completed_at": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": (datetime.now(timezone.utc) - task_start).total_seconds(),
            }

    return asyncio.run(_run_ingestion())


@celery_app.task(
    bind=True,
    name="crypto_newsletter.core.scheduling.tasks.health_check",
    max_retries=1,
)
def health_check(self) -> Dict[str, Any]:
    """
    Scheduled health check task including Redis connection monitoring.

    Returns:
        Dict with comprehensive health check results
    """
    async def _run_health_check():
        try:
            logger.debug("Running scheduled health check")

            # Check pipeline health
            pipeline_status = await pipeline_health_check()

            # Check Redis/Celery connection health
            celery_status = check_celery_health(celery_app)

            # Combine results
            overall_status = "healthy"
            if (pipeline_status["status"] != "healthy" or
                celery_status["overall_status"] != "healthy"):
                overall_status = "unhealthy"

            health_status = {
                "status": overall_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": {
                    "pipeline": pipeline_status,
                    "celery_redis": celery_status,
                }
            }

            if overall_status != "healthy":
                logger.warning(f"Health check detected issues: {health_status}")
            else:
                logger.debug("Health check passed")

            return health_status

        except Exception as exc:
            logger.error(f"Health check failed: {exc}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }

    return asyncio.run(_run_health_check())


@celery_app.task(
    bind=True,
    name="crypto_newsletter.core.scheduling.tasks.cleanup_old_articles",
    max_retries=2,
)
def cleanup_old_articles(
    self,
    days_to_keep: int = 30,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Scheduled task to clean up old articles.
    
    Args:
        days_to_keep: Number of days of articles to keep
        dry_run: If True, only count articles that would be deleted
    
    Returns:
        Dict with cleanup results
    """
    async def _run_cleanup():
        try:
            logger.info(f"Starting article cleanup - days_to_keep: {days_to_keep}, dry_run: {dry_run}")

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            async with get_db_session() as db:
                repo = ArticleRepository(db)

                if dry_run:
                    # Count articles that would be deleted
                    from sqlalchemy import select, func
                    from crypto_newsletter.shared.models import Article

                    query = select(func.count(Article.id)).where(
                        Article.published_on < cutoff_date,
                        Article.status == "ACTIVE"
                    )
                    result = await db.execute(query)
                    count = result.scalar() or 0

                    logger.info(f"Cleanup dry run: {count} articles would be deleted")
                    return {
                        "success": True,
                        "dry_run": True,
                        "articles_to_delete": count,
                        "cutoff_date": cutoff_date.isoformat(),
                    }

                else:
                    # Actually delete old articles (mark as DELETED)
                    from sqlalchemy import update
                    from crypto_newsletter.shared.models import Article

                    query = update(Article).where(
                        Article.published_on < cutoff_date,
                        Article.status == "ACTIVE"
                    ).values(
                        status="DELETED",
                        updated_on=datetime.now(timezone.utc)
                    )

                    result = await db.execute(query)
                    await db.commit()

                    deleted_count = result.rowcount
                    logger.info(f"Cleanup completed: {deleted_count} articles marked as deleted")

                    return {
                        "success": True,
                        "dry_run": False,
                        "articles_deleted": deleted_count,
                        "cutoff_date": cutoff_date.isoformat(),
                    }

        except Exception as exc:
            logger.error(f"Article cleanup failed: {exc}")

            if self.request.retries < self.max_retries:
                retry_delay = 600  # 10 minutes
                logger.warning(f"Retrying cleanup in {retry_delay} seconds")
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "success": False,
                "error": str(exc),
                "cutoff_date": cutoff_date.isoformat() if 'cutoff_date' in locals() else None,
            }

    return asyncio.run(_run_cleanup())


@celery_app.task(
    name="crypto_newsletter.core.scheduling.tasks.manual_ingest",
    max_retries=1,
)
def manual_ingest(
    limit: Optional[int] = None,
    hours_back: int = 24,
    categories: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Manual ingestion task (can be triggered via API or CLI).

    Args:
        limit: Maximum number of articles to fetch
        hours_back: How many hours back to look for articles
        categories: List of categories to filter by

    Returns:
        Dict with ingestion results
    """
    async def _run_ingestion():
        pipeline = ArticleIngestionPipeline()
        return await pipeline.run_full_ingestion(
            limit=limit,
            hours_back=hours_back,
            categories=categories,
        )

    return asyncio.run(_run_ingestion())


# Task monitoring utilities
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a specific task."""
    result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None,
        "date_done": result.date_done.isoformat() if result.date_done else None,
    }


def get_active_tasks() -> Dict[str, Any]:
    """Get information about currently active tasks."""
    inspect = celery_app.control.inspect()
    
    return {
        "active": inspect.active(),
        "scheduled": inspect.scheduled(),
        "reserved": inspect.reserved(),
    }


def cancel_task(task_id: str) -> bool:
    """Cancel a specific task."""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Task {task_id} cancelled successfully")
        return True
    except Exception as exc:
        logger.error(f"Failed to cancel task {task_id}: {exc}")
        return False
