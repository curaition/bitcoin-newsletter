"""Batch processing error handling and recovery system."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from crypto_newsletter.analysis.tasks import analyze_article_task
from crypto_newsletter.newsletter.batch.storage import BatchStorageManager
from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(queue="batch_processing")
def recover_failed_batch_articles() -> dict[str, Any]:
    """Recover and retry failed article analyses."""

    async def _recover_failed_articles() -> dict[str, Any]:
        """Internal async function for failure recovery."""

        recovery_start = datetime.utcnow()
        logger.info("Starting failed article recovery")

        try:
            async with get_db_session() as db:
                storage = BatchStorageManager()

                # Get failed articles from recent sessions
                failed_articles = await get_failed_batch_articles(db)

                if not failed_articles:
                    return {
                        "status": "no_failures",
                        "message": "No failed articles found for recovery",
                        "recovery_timestamp": recovery_start.isoformat(),
                    }

                recovery_results = []
                successful_recoveries = 0
                failed_recoveries = 0

                for article_info in failed_articles:
                    try:
                        article_id = article_info["article_id"]
                        session_id = article_info["session_id"]
                        batch_number = article_info["batch_number"]

                        # Calculate retry delay based on failure count
                        retry_delay = calculate_retry_delay(
                            article_info.get("failure_count", 1)
                        )

                        logger.info(
                            f"Recovering article {article_id} with {retry_delay}s delay"
                        )

                        # Retry with exponential backoff
                        result = analyze_article_task.apply_async(
                            args=[article_id], countdown=retry_delay
                        )

                        recovery_results.append(
                            {
                                "article_id": article_id,
                                "session_id": session_id,
                                "batch_number": batch_number,
                                "retry_task_id": result.id,
                                "retry_delay": retry_delay,
                                "status": "retry_scheduled",
                            }
                        )

                        successful_recoveries += 1

                        # Update failure tracking
                        await update_article_failure_tracking(
                            db, article_id, session_id, batch_number, "RETRY_SCHEDULED"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to recover article {article_info['article_id']}: {e}"
                        )
                        failed_recoveries += 1

                        recovery_results.append(
                            {
                                "article_id": article_info["article_id"],
                                "status": "recovery_failed",
                                "error": str(e),
                            }
                        )

                processing_time = (datetime.utcnow() - recovery_start).total_seconds()

                logger.info(
                    f"Recovery completed - "
                    f"Successful: {successful_recoveries}, Failed: {failed_recoveries}, "
                    f"Time: {processing_time:.2f}s"
                )

                return {
                    "status": "completed",
                    "articles_found": len(failed_articles),
                    "successful_recoveries": successful_recoveries,
                    "failed_recoveries": failed_recoveries,
                    "recovery_results": recovery_results,
                    "processing_time_seconds": processing_time,
                    "recovery_timestamp": recovery_start.isoformat(),
                }

        except Exception as exc:
            logger.error(f"Article recovery failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "recovery_timestamp": recovery_start.isoformat(),
            }

    return asyncio.run(_recover_failed_articles())


async def get_failed_batch_articles(db) -> list[dict[str, Any]]:
    """Get articles that failed in batch processing and are eligible for retry."""
    try:
        from sqlalchemy import text

        # Get failed articles from the last 24 hours
        query = text(
            """
            SELECT DISTINCT
                unnest(bpr.article_ids) as article_id,
                bpr.session_id,
                bpr.batch_number,
                bpr.error_message,
                bpr.completed_at,
                bps.started_at as session_started
            FROM batch_processing_records bpr
            JOIN batch_processing_sessions bps ON bpr.session_id = bps.session_id
            WHERE bpr.status = 'FAILED'
              AND bpr.articles_failed > 0
              AND bpr.completed_at > NOW() - INTERVAL '24 hours'
              AND bps.status != 'CANCELLED'
            ORDER BY bpr.completed_at DESC
            LIMIT 50
        """
        )

        result = await db.execute(query)
        rows = result.fetchall()

        failed_articles = []
        for row in rows:
            # Check if article still needs analysis
            article_analyzed = await check_if_article_analyzed(db, row.article_id)

            if not article_analyzed:
                failed_articles.append(
                    {
                        "article_id": row.article_id,
                        "session_id": row.session_id,
                        "batch_number": row.batch_number,
                        "error_message": row.error_message,
                        "failed_at": row.completed_at.isoformat()
                        if row.completed_at
                        else None,
                        "session_started": row.session_started.isoformat()
                        if row.session_started
                        else None,
                        "failure_count": 1,  # Could be enhanced to track actual failure count
                    }
                )

        logger.info(
            f"Found {len(failed_articles)} failed articles eligible for recovery"
        )
        return failed_articles

    except Exception as e:
        logger.error(f"Failed to get failed batch articles: {e}")
        return []


async def check_if_article_analyzed(db, article_id: int) -> bool:
    """Check if an article has been successfully analyzed."""
    try:
        from sqlalchemy import text

        query = text(
            """
            SELECT 1 FROM article_analyses
            WHERE article_id = :article_id
              AND analysis_confidence > 0.5
            LIMIT 1
        """
        )

        result = await db.execute(query, {"article_id": article_id})
        return result.fetchone() is not None

    except Exception:
        return False


def calculate_retry_delay(failure_count: int) -> int:
    """Calculate retry delay based on failure count using exponential backoff."""
    base_delay = 300  # 5 minutes
    max_delay = 3600  # 1 hour

    delay = base_delay * (2 ** (failure_count - 1))
    return min(delay, max_delay)


async def update_article_failure_tracking(
    db, article_id: int, session_id: str, batch_number: int, status: str
) -> None:
    """Update failure tracking for an article."""
    try:
        # This could be enhanced with a dedicated failure tracking table
        # For now, just log the update
        logger.info(
            f"Updated failure tracking for article {article_id} "
            f"in session {session_id}, batch {batch_number}: {status}"
        )

    except Exception as e:
        logger.error(f"Failed to update failure tracking: {e}")


@celery_app.task(queue="batch_processing")
def cleanup_stalled_batches() -> dict[str, Any]:
    """Clean up batches that have been processing for too long."""

    async def _cleanup_stalled() -> dict[str, Any]:
        """Internal async function for stalled batch cleanup."""

        cleanup_start = datetime.utcnow()
        logger.info("Starting stalled batch cleanup")

        try:
            async with get_db_session() as db:
                storage = BatchStorageManager()

                # Find batches that have been processing for more than 1 hour
                stalled_threshold = datetime.utcnow() - timedelta(hours=1)

                stalled_batches = await get_stalled_batches(db, stalled_threshold)

                if not stalled_batches:
                    return {
                        "status": "no_stalled_batches",
                        "message": "No stalled batches found",
                        "cleanup_timestamp": cleanup_start.isoformat(),
                    }

                cleanup_results = []

                for batch_info in stalled_batches:
                    try:
                        session_id = batch_info["session_id"]
                        batch_number = batch_info["batch_number"]

                        # Mark batch as failed
                        await storage.update_batch_record_status(
                            db,
                            session_id,
                            batch_number,
                            "FAILED",
                            error_message="Batch processing timeout - marked as stalled",
                        )

                        cleanup_results.append(
                            {
                                "session_id": session_id,
                                "batch_number": batch_number,
                                "action": "marked_failed",
                                "reason": "processing_timeout",
                            }
                        )

                        logger.info(
                            f"Marked stalled batch {batch_number} in session {session_id} as failed"
                        )

                    except Exception as e:
                        logger.error(f"Failed to cleanup stalled batch: {e}")
                        cleanup_results.append(
                            {
                                "session_id": batch_info["session_id"],
                                "batch_number": batch_info["batch_number"],
                                "action": "cleanup_failed",
                                "error": str(e),
                            }
                        )

                processing_time = (datetime.utcnow() - cleanup_start).total_seconds()

                return {
                    "status": "completed",
                    "stalled_batches_found": len(stalled_batches),
                    "cleanup_results": cleanup_results,
                    "processing_time_seconds": processing_time,
                    "cleanup_timestamp": cleanup_start.isoformat(),
                }

        except Exception as exc:
            logger.error(f"Stalled batch cleanup failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "cleanup_timestamp": cleanup_start.isoformat(),
            }

    return asyncio.run(_cleanup_stalled())


async def get_stalled_batches(db, stalled_threshold: datetime) -> list[dict[str, Any]]:
    """Get batches that have been processing for too long."""
    try:
        from sqlalchemy import text

        query = text(
            """
            SELECT
                session_id,
                batch_number,
                started_at,
                article_ids
            FROM batch_processing_records
            WHERE status = 'PROCESSING'
              AND started_at < :threshold
            ORDER BY started_at ASC
        """
        )

        result = await db.execute(query, {"threshold": stalled_threshold})
        rows = result.fetchall()

        stalled_batches = []
        for row in rows:
            stalled_batches.append(
                {
                    "session_id": row.session_id,
                    "batch_number": row.batch_number,
                    "started_at": row.started_at.isoformat()
                    if row.started_at
                    else None,
                    "article_count": len(row.article_ids) if row.article_ids else 0,
                }
            )

        return stalled_batches

    except Exception as e:
        logger.error(f"Failed to get stalled batches: {e}")
        return []
