"""Progress tracking service for newsletter generation."""

from datetime import datetime
from typing import Any, Optional

from crypto_newsletter.newsletter.models.progress import NewsletterGenerationProgress
from crypto_newsletter.shared.database.connection import get_db_session
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProgressTracker:
    """Service for tracking newsletter generation progress."""

    def __init__(self):
        self.db: Optional[AsyncSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.db = get_db_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.db:
            await self.db.close()

    async def initialize_progress(
        self, task_id: str, articles_count: int, estimated_completion: datetime
    ) -> None:
        """Initialize progress tracking for a new generation task."""
        try:
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
            logger.info(f"Initialized progress tracking for task {task_id}")

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
