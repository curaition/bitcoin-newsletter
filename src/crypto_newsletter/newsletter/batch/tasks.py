"""Batch processing Celery tasks for newsletter system."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

# analyze_article_task imported inside function to avoid circular imports
from crypto_newsletter.newsletter.batch.config import BatchProcessingConfig
from crypto_newsletter.newsletter.batch.identifier import BatchArticleIdentifier
from crypto_newsletter.newsletter.batch.storage import BatchStorageManager
from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_sync_db_session

logger = logging.getLogger(__name__)


class BudgetExceededException(Exception):
    """Raised when batch processing exceeds budget limits."""

    pass


class NewsletterGenerationException(Exception):
    """Raised when newsletter generation fails."""

    pass


@celery_app.task(bind=True, max_retries=3, queue="batch_processing")
async def batch_analyze_articles_async(
    self, article_ids: list[int], batch_number: int, session_id: str
) -> dict[str, Any]:
    """
    Process a batch of articles for analysis using async approach.

    This async task eliminates event loop conflicts by running the entire
    batch processing pipeline in a single async context.

    Args:
        article_ids: List of article IDs to process
        batch_number: Batch number in the session
        session_id: Batch processing session ID

    Returns:
        Dict with batch processing results
    """

    async def _process_batch_async() -> dict[str, Any]:
        """Internal async function for batch processing."""
        from crypto_newsletter.analysis.tasks import analyze_article_direct
        from crypto_newsletter.analysis.dependencies import CostTracker
        from crypto_newsletter.shared.database.connection import get_db_session

        batch_start = datetime.utcnow()
        logger.info(
            f"Starting async batch {batch_number} with {len(article_ids)} articles (session: {session_id})"
        )

        try:
            async with get_db_session() as db:
                # Initialize cost tracker for this batch
                cost_tracker = CostTracker(
                    daily_budget=BatchProcessingConfig.MAX_TOTAL_BUDGET
                )

                # TODO: Update batch record status to PROCESSING (async version needed)
                # TODO: Check budget constraint before processing (async version needed)
                # For now, we'll focus on the core analysis functionality

                # Process individual articles
                results = []
                batch_cost = 0.0
                articles_processed = 0
                articles_failed = 0

                for article_id in article_ids:
                    try:
                        logger.info(
                            f"Processing article {article_id} in batch {batch_number}"
                        )

                        # Call direct async analysis function
                        task_result = await analyze_article_direct(
                            article_id=article_id,
                            db=db,
                            cost_tracker=cost_tracker
                        )

                        if task_result.get("success", False):
                            articles_processed += 1
                            actual_cost = task_result.get("costs", {}).get("total", 0.0)
                            batch_cost += actual_cost

                            results.append(
                                {
                                    "article_id": article_id,
                                    "status": "success",
                                    "cost": actual_cost,
                                    "signals_found": task_result.get("processing_metadata", {}).get("signals_found", 0),
                                }
                            )
                        else:
                            articles_failed += 1
                            results.append(
                                {
                                    "article_id": article_id,
                                    "status": "failed",
                                    "error": task_result.get("error", "Unknown error"),
                                }
                            )

                        # Brief pause between articles to manage load
                        await asyncio.sleep(2)

                    except Exception as e:
                        logger.error(f"Failed to process article {article_id}: {e}")
                        articles_failed += 1
                        results.append(
                            {
                                "article_id": article_id,
                                "status": "failed",
                                "error": str(e),
                            }
                        )

                # Update batch record with results
                batch_completed = datetime.utcnow()
                # TODO: Implement async storage manager methods
                # For now, we'll skip the database updates and focus on the core analysis

                # Commit the analysis results that were stored
                await db.commit()

                processing_time = (batch_completed - batch_start).total_seconds()

                logger.info(
                    f"Batch {batch_number} completed - "
                    f"Processed: {articles_processed}, Failed: {articles_failed}, "
                    f"Cost: ${batch_cost:.4f}, Time: {processing_time:.2f}s"
                )

                return {
                    "batch_number": batch_number,
                    "session_id": session_id,
                    "articles_processed": articles_processed,
                    "articles_failed": articles_failed,
                    "estimated_batch_cost": batch_cost,
                    "processing_time_seconds": processing_time,
                    "task_results": results,
                    "status": "completed",
                }

        except Exception as exc:
            logger.error(f"Async batch {batch_number} failed: {exc}")

            # TODO: Update batch record with failure using async storage manager
            # For now, we'll skip the database update and focus on the core functionality

            # Retry logic
            if self.request.retries < self.max_retries:
                retry_delay = 300 * (self.request.retries + 1)  # Exponential backoff
                logger.warning(
                    f"Retrying batch {batch_number} in {retry_delay} seconds"
                )
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "batch_number": batch_number,
                "session_id": session_id,
                "status": "failed",
                "error": str(exc),
                "retries_exhausted": True,
            }

    # Run the async batch processing
    return await _process_batch_async()


@celery_app.task(bind=True, queue="batch_processing")
def initiate_batch_processing(self, force_processing: bool = False) -> dict[str, Any]:
    """
    Start the complete batch processing workflow.

    Args:
        force_processing: Process even if insufficient articles or budget constraints

    Returns:
        Dict with batch processing initiation results
    """

    def _initiate_processing() -> dict[str, Any]:
        """Internal function for batch processing initiation with sync database operations."""

        initiation_start = datetime.utcnow()
        logger.info("Starting batch processing initiation")

        try:
            with get_sync_db_session() as db:
                identifier = BatchArticleIdentifier()
                storage = BatchStorageManager()

                # Step 1: Get articles to process
                article_ids = identifier.get_analyzable_articles_sync(db)

                if len(article_ids) == 0:
                    return {
                        "status": "no_articles",
                        "message": "No articles found for processing",
                        "initiation_time": initiation_start.isoformat(),
                    }

                # Step 2: Validate articles and budget
                validation = identifier.validate_articles_for_processing_sync(
                    db, article_ids
                )

                if (
                    not validation["validation_summary"]["validation_passed"]
                    and not force_processing
                ):
                    return {
                        "status": "validation_failed",
                        "validation_summary": validation["validation_summary"],
                        "message": f"Only {validation['validation_summary']['valid_count']} valid articles found",
                        "initiation_time": initiation_start.isoformat(),
                    }

                # Use only valid articles
                valid_article_ids = [a["id"] for a in validation["valid_articles"]]

                # Step 3: Budget validation
                budget_check = BatchProcessingConfig.validate_budget(
                    len(valid_article_ids)
                )

                if not budget_check["within_budget"] and not force_processing:
                    return {
                        "status": "budget_exceeded",
                        "budget_check": budget_check,
                        "message": f"Estimated cost ${budget_check['estimated_cost']:.4f} exceeds budget ${budget_check['max_budget']:.2f}",
                        "initiation_time": initiation_start.isoformat(),
                    }

                # Step 4: Create batches
                article_chunks = [
                    valid_article_ids[i : i + BatchProcessingConfig.BATCH_SIZE]
                    for i in range(
                        0, len(valid_article_ids), BatchProcessingConfig.BATCH_SIZE
                    )
                ]

                # Step 5: Initialize batch processing session
                session_id = str(uuid.uuid4())
                session = storage.create_batch_session_sync(
                    db,
                    session_id,
                    len(valid_article_ids),
                    len(article_chunks),
                    budget_check["estimated_cost"],
                )

                # Step 6: Create batch records
                batch_records = []
                for i, chunk in enumerate(article_chunks, 1):
                    batch_record = storage.create_batch_record_sync(
                        db,
                        session_id,
                        i,
                        chunk,
                        len(chunk) * BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE,
                    )
                    batch_records.append(batch_record)

                # Step 7: Launch batches immediately (no delays in initiation)
                batch_tasks = []
                for i, chunk in enumerate(article_chunks, 1):
                    # Launch batch processing task with countdown for staggered execution
                    # Each batch will start with a delay based on its number
                    countdown = (i - 1) * BatchProcessingConfig.BATCH_DELAY
                    task = batch_analyze_articles_async.apply_async(
                        args=[chunk, i, session_id],
                        countdown=countdown
                    )
                    batch_tasks.append(
                        {
                            "batch_number": i,
                            "task_id": task.id,
                            "article_count": len(chunk),
                            "scheduled_delay": countdown,
                        }
                    )

                processing_time = (datetime.utcnow() - initiation_start).total_seconds()

                logger.info(
                    f"Batch processing initiated - Session: {session_id}, "
                    f"Batches: {len(article_chunks)}, Articles: {len(valid_article_ids)}, "
                    f"Estimated cost: ${budget_check['estimated_cost']:.4f}"
                )

                return {
                    "status": "initiated",
                    "session_id": session_id,
                    "total_batches": len(article_chunks),
                    "total_articles": len(valid_article_ids),
                    "batch_tasks": batch_tasks,
                    "estimated_total_cost": budget_check["estimated_cost"],
                    "budget_utilization": budget_check["budget_utilization"],
                    "initiation_time_seconds": processing_time,
                    "validation_summary": validation["validation_summary"],
                    "initiation_timestamp": initiation_start.isoformat(),
                }

        except Exception as exc:
            logger.error(f"Batch processing initiation failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "initiation_timestamp": initiation_start.isoformat(),
            }

    # Run the synchronous batch processing initiation
    return _initiate_processing()
