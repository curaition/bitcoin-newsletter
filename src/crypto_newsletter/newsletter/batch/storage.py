"""Batch processing storage and database operations."""

import logging
from datetime import datetime
from typing import Optional

from crypto_newsletter.shared.models import (
    BatchProcessingRecord,
    BatchProcessingSession,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class BatchStorageManager:
    """Manages database operations for batch processing."""

    async def create_batch_session(
        self,
        db: AsyncSession,
        session_id: str,
        total_articles: int,
        total_batches: int,
        estimated_cost: float,
    ) -> BatchProcessingSession:
        """Create a new batch processing session."""
        try:
            session = BatchProcessingSession(
                session_id=session_id,
                total_articles=total_articles,
                total_batches=total_batches,
                estimated_cost=estimated_cost,
                status="INITIATED",
                started_at=datetime.utcnow(),
            )

            db.add(session)
            await db.commit()
            await db.refresh(session)

            logger.info(
                f"Created batch session {session_id} for {total_articles} articles"
            )
            return session

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create batch session: {e}")
            raise

    async def create_batch_record(
        self,
        db: AsyncSession,
        session_id: str,
        batch_number: int,
        article_ids: list[int],
        estimated_cost: float,
    ) -> BatchProcessingRecord:
        """Create a new batch processing record."""
        try:
            record = BatchProcessingRecord(
                session_id=session_id,
                batch_number=batch_number,
                article_ids=article_ids,
                estimated_cost=estimated_cost,
                status="PENDING",
            )

            db.add(record)
            await db.commit()
            await db.refresh(record)

            logger.info(f"Created batch record {batch_number} for session {session_id}")
            return record

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create batch record: {e}")
            raise

    async def update_batch_record_status(
        self,
        db: AsyncSession,
        session_id: str,
        batch_number: int,
        status: str,
        started_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update batch record status."""
        try:
            update_data = {"status": status}

            if started_at:
                update_data["started_at"] = started_at

            if error_message:
                update_data["error_message"] = error_message

            stmt = (
                update(BatchProcessingRecord)
                .where(
                    BatchProcessingRecord.session_id == session_id,
                    BatchProcessingRecord.batch_number == batch_number,
                )
                .values(**update_data)
            )

            await db.execute(stmt)
            await db.commit()

            logger.info(f"Updated batch {batch_number} status to {status}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update batch record status: {e}")
            raise

    async def update_batch_record_completion(
        self,
        db: AsyncSession,
        session_id: str,
        batch_number: int,
        articles_processed: int,
        articles_failed: int,
        actual_cost: float,
        completed_at: datetime,
    ) -> None:
        """Update batch record with completion data."""
        try:
            stmt = (
                update(BatchProcessingRecord)
                .where(
                    BatchProcessingRecord.session_id == session_id,
                    BatchProcessingRecord.batch_number == batch_number,
                )
                .values(
                    status="COMPLETED",
                    articles_processed=articles_processed,
                    articles_failed=articles_failed,
                    actual_cost=actual_cost,
                    completed_at=completed_at,
                )
            )

            await db.execute(stmt)
            await db.commit()

            logger.info(
                f"Updated batch {batch_number} completion: "
                f"processed={articles_processed}, failed={articles_failed}, cost=${actual_cost:.4f}"
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update batch record completion: {e}")
            raise

    async def update_session_actual_cost(
        self, db: AsyncSession, session_id: str, additional_cost: float
    ) -> None:
        """Update session actual cost by adding additional cost."""
        try:
            # Get current actual cost
            stmt = select(BatchProcessingSession.actual_cost).where(
                BatchProcessingSession.session_id == session_id
            )
            result = await db.execute(stmt)
            current_cost = result.scalar() or 0.0

            # Update with new total
            new_cost = current_cost + additional_cost

            update_stmt = (
                update(BatchProcessingSession)
                .where(BatchProcessingSession.session_id == session_id)
                .values(actual_cost=new_cost)
            )

            await db.execute(update_stmt)
            await db.commit()

            logger.info(f"Updated session {session_id} actual cost to ${new_cost:.4f}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update session actual cost: {e}")
            raise

    async def get_session_actual_cost(self, db: AsyncSession, session_id: str) -> float:
        """Get current actual cost for a session."""
        try:
            stmt = select(BatchProcessingSession.actual_cost).where(
                BatchProcessingSession.session_id == session_id
            )
            result = await db.execute(stmt)
            return result.scalar() or 0.0

        except Exception as e:
            logger.error(f"Failed to get session actual cost: {e}")
            return 0.0

    async def get_batch_session_with_records(
        self, db: AsyncSession, session_id: str
    ) -> Optional[BatchProcessingSession]:
        """Get batch session with all its records."""
        try:
            stmt = (
                select(BatchProcessingSession)
                .options(selectinload(BatchProcessingSession.batch_records))
                .where(BatchProcessingSession.session_id == session_id)
            )

            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get batch session: {e}")
            return None

    async def get_active_batch_sessions(
        self, db: AsyncSession
    ) -> list[BatchProcessingSession]:
        """Get all active batch processing sessions."""
        try:
            stmt = (
                select(BatchProcessingSession)
                .where(BatchProcessingSession.status.in_(["INITIATED", "PROCESSING"]))
                .options(selectinload(BatchProcessingSession.batch_records))
            )

            result = await db.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get active batch sessions: {e}")
            return []

    async def finalize_batch_session(self, db: AsyncSession, session_id: str) -> None:
        """Finalize a batch processing session."""
        try:
            # Check if all batches are completed
            session = await self.get_batch_session_with_records(db, session_id)

            if not session:
                logger.warning(f"Session {session_id} not found for finalization")
                return

            completed_batches = sum(
                1 for record in session.batch_records if record.status == "COMPLETED"
            )
            failed_batches = sum(
                1 for record in session.batch_records if record.status == "FAILED"
            )
            total_batches = len(session.batch_records)

            # Determine final status
            if completed_batches == total_batches:
                final_status = "COMPLETED"
            elif completed_batches + failed_batches == total_batches:
                final_status = "COMPLETED"  # Some failures but all processed
            else:
                final_status = "PROCESSING"  # Still in progress
                return

            # Update session status
            stmt = (
                update(BatchProcessingSession)
                .where(BatchProcessingSession.session_id == session_id)
                .values(status=final_status, completed_at=datetime.utcnow())
            )

            await db.execute(stmt)
            await db.commit()

            logger.info(
                f"Finalized session {session_id}: {completed_batches}/{total_batches} batches completed"
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to finalize batch session: {e}")
            raise
