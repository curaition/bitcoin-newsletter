"""Progress tracking service for newsletter generation."""

from datetime import datetime, timedelta
from typing import Any, Optional

from crypto_newsletter.newsletter.models.progress import NewsletterGenerationProgress
from crypto_newsletter.shared.database.connection import get_db_session
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProgressTracker:
    """Service for tracking newsletter generation progress."""

    def __init__(self):
        self.db_session_manager = None
        self.db: Optional[AsyncSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.db_session_manager = get_db_session()
        self.db = await self.db_session_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.db_session_manager:
            await self.db_session_manager.__aexit__(exc_type, exc_val, exc_tb)

    async def initialize_progress(
        self, task_id: str, articles_count: int, estimated_completion: datetime
    ) -> None:
        """Initialize progress tracking for a new generation task."""
        try:
            # Check if progress record already exists (for retries)
            stmt = select(NewsletterGenerationProgress).where(
                NewsletterGenerationProgress.task_id == task_id
            )
            result = await self.db.execute(stmt)
            existing_progress = result.scalar_one_or_none()

            if existing_progress:
                # Reset existing record for retry
                logger.info(f"Resetting existing progress record for task {task_id}")
                existing_progress.current_step = "selection"
                existing_progress.step_progress = 0.0
                existing_progress.overall_progress = 0.0
                existing_progress.articles_being_processed = []
                existing_progress.estimated_completion = estimated_completion
                existing_progress.step_details = {
                    "articles_count": articles_count,
                    "status": "Initializing newsletter generation (retry)",
                    "step_description": "Preparing to analyze articles and select stories",
                }
                existing_progress.intermediate_results = {}
                existing_progress.quality_metrics = {}
                existing_progress.status = "in_progress"
                existing_progress.updated_at = datetime.utcnow()
            else:
                # Create new progress record
                logger.info(f"Creating new progress record for task {task_id}")
                progress = NewsletterGenerationProgress(
                    task_id=task_id,
                    current_step="selection",
                    step_progress=0.0,
                    overall_progress=0.0,
                    articles_being_processed=[],
                    estimated_completion=estimated_completion,
                    step_details={
                        "articles_count": articles_count,
                        "status": "Initializing newsletter generation",
                        "step_description": "Preparing to analyze articles and select stories",
                    },
                    status="in_progress",
                )
                self.db.add(progress)

            await self.db.commit()
            logger.info(f"Successfully initialized progress tracking for task {task_id}")

        except Exception as e:
            logger.error(f"Failed to initialize progress for task {task_id}: {e}")
            await self.db.rollback()
            raise

    async def update_progress(
        self,
        task_id: str,
        step: str,
        step_progress: float,
        step_details: dict[str, Any],
        intermediate_result: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update progress for a specific step."""
        try:
            # Calculate overall progress based on step
            step_weights = {
                "selection": (0.0, 0.33),
                "synthesis": (0.33, 0.66),
                "writing": (0.66, 0.90),
                "storage": (0.90, 1.0),
            }

            start_weight, end_weight = step_weights.get(step, (0.0, 1.0))
            overall_progress = start_weight + (
                step_progress * (end_weight - start_weight)
            )

            # Get existing progress record
            stmt = select(NewsletterGenerationProgress).where(
                NewsletterGenerationProgress.task_id == task_id
            )
            result = await self.db.execute(stmt)
            progress = result.scalar_one_or_none()

            if progress:
                progress.current_step = step
                progress.step_progress = step_progress
                progress.overall_progress = overall_progress
                progress.step_details = step_details
                progress.updated_at = datetime.utcnow()

                if intermediate_result:
                    # Merge with existing intermediate results
                    current_results = progress.intermediate_results or {}
                    current_results[step] = intermediate_result
                    progress.intermediate_results = current_results

                await self.db.commit()
                logger.debug(
                    f"Updated progress for task {task_id}: {step} - {step_progress:.2f}"
                )
            else:
                logger.warning(f"Progress record not found for task {task_id}")

        except Exception as e:
            logger.error(f"Failed to update progress for task {task_id}: {e}")
            await self.db.rollback()
            raise

    async def complete_generation(
        self, task_id: str, newsletter_id: int, final_details: dict[str, Any]
    ) -> None:
        """Mark generation as complete."""
        try:
            stmt = select(NewsletterGenerationProgress).where(
                NewsletterGenerationProgress.task_id == task_id
            )
            result = await self.db.execute(stmt)
            progress = result.scalar_one_or_none()

            if progress:
                progress.status = "complete"
                progress.overall_progress = 1.0
                progress.step_details = {
                    **final_details,
                    "newsletter_id": newsletter_id,
                    "completed_at": datetime.utcnow().isoformat(),
                }
                progress.updated_at = datetime.utcnow()

                await self.db.commit()
                logger.info(
                    f"Marked task {task_id} as complete with newsletter {newsletter_id}"
                )
            else:
                logger.warning(f"Progress record not found for task {task_id}")

        except Exception as e:
            logger.error(f"Failed to complete progress for task {task_id}: {e}")
            await self.db.rollback()
            raise

    async def mark_failed(
        self, task_id: str, error_message: str, error_details: dict[str, Any]
    ) -> None:
        """Mark generation as failed."""
        try:
            stmt = select(NewsletterGenerationProgress).where(
                NewsletterGenerationProgress.task_id == task_id
            )
            result = await self.db.execute(stmt)
            progress = result.scalar_one_or_none()

            if progress:
                progress.status = "failed"
                progress.step_details = {
                    **error_details,
                    "error_message": error_message,
                    "failed_at": datetime.utcnow().isoformat(),
                }
                progress.updated_at = datetime.utcnow()

                await self.db.commit()
                logger.error(f"Marked task {task_id} as failed: {error_message}")
            else:
                logger.warning(f"Progress record not found for task {task_id}")

        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {e}")
            await self.db.rollback()
            raise

    async def get_progress(
        self, task_id: str
    ) -> Optional[NewsletterGenerationProgress]:
        """Get current progress for a task."""
        try:
            stmt = select(NewsletterGenerationProgress).where(
                NewsletterGenerationProgress.task_id == task_id
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get progress for task {task_id}: {e}")
            return None

    def get_current_step(self, task_id: str) -> str:
        """Get current step for a task (synchronous helper)."""
        # This is a helper method for error reporting
        return "unknown"

    async def cleanup_old_progress_records(self, hours_old: int = 24) -> int:
        """
        Clean up old progress records to prevent database bloat.

        Args:
            hours_old: Remove records older than this many hours

        Returns:
            Number of records cleaned up
        """
        try:
            from sqlalchemy import delete

            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)

            # Delete old completed, failed, or stuck in_progress records
            stmt = delete(NewsletterGenerationProgress).where(
                (NewsletterGenerationProgress.created_at < cutoff_time) &
                (
                    (NewsletterGenerationProgress.status == "complete") |
                    (NewsletterGenerationProgress.status == "failed") |
                    (
                        (NewsletterGenerationProgress.status == "in_progress") &
                        (NewsletterGenerationProgress.updated_at < cutoff_time)
                    )
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            cleaned_count = result.rowcount
            logger.info(f"Cleaned up {cleaned_count} old progress records (older than {hours_old}h)")

            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup old progress records: {e}")
            await self.db.rollback()
            raise

    @classmethod
    async def cleanup_old_records_standalone(cls, hours_old: int = 24) -> int:
        """
        Standalone method to cleanup old progress records without existing session.

        Args:
            hours_old: Remove records older than this many hours

        Returns:
            Number of records cleaned up
        """
        async with get_db_session() as db:
            tracker = cls()
            tracker.db = db
            return await tracker.cleanup_old_progress_records(hours_old)
