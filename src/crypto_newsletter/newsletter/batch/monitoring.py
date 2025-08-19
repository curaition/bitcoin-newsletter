"""Batch processing monitoring and progress tracking."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from crypto_newsletter.newsletter.batch.config import BatchProcessingConfig
from crypto_newsletter.newsletter.batch.storage import BatchStorageManager
from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_db_session

logger = logging.getLogger(__name__)


@celery_app.task(queue="monitoring")
def monitor_batch_processing() -> dict[str, Any]:
    """Monitor active batch processing sessions."""

    async def _monitor_processing() -> dict[str, Any]:
        """Internal async monitoring function."""

        monitoring_start = datetime.utcnow()
        logger.info("Starting batch processing monitoring")

        try:
            async with get_db_session() as db:
                storage = BatchStorageManager()

                # Get all active sessions
                active_sessions = await storage.get_active_batch_sessions(db)

                monitoring_results = {
                    "monitoring_timestamp": monitoring_start.isoformat(),
                    "active_sessions_count": len(active_sessions),
                    "session_details": [],
                    "alerts": [],
                    "actions_taken": [],
                }

                for session in active_sessions:
                    session_status = await calculate_session_progress(
                        db, session.session_id
                    )
                    monitoring_results["session_details"].append(session_status)

                    # Check for alerts
                    alerts = await check_session_alerts(session_status)
                    monitoring_results["alerts"].extend(alerts)

                    # Take actions if needed
                    actions = await handle_session_issues(db, session, session_status)
                    monitoring_results["actions_taken"].extend(actions)

                # Update monitoring metrics
                await update_monitoring_metrics(db, monitoring_results)

                processing_time = (datetime.utcnow() - monitoring_start).total_seconds()
                monitoring_results["monitoring_time_seconds"] = processing_time

                logger.info(
                    f"Batch monitoring completed - "
                    f"Sessions: {len(active_sessions)}, "
                    f"Alerts: {len(monitoring_results['alerts'])}, "
                    f"Time: {processing_time:.2f}s"
                )

                return monitoring_results

        except Exception as exc:
            logger.error(f"Batch processing monitoring failed: {exc}")
            return {
                "status": "monitoring_failed",
                "error": str(exc),
                "monitoring_timestamp": monitoring_start.isoformat(),
            }

    return asyncio.run(_monitor_processing())


async def calculate_session_progress(db, session_id: str) -> dict[str, Any]:
    """Calculate detailed progress for a batch processing session."""
    try:
        storage = BatchStorageManager()
        session = await storage.get_batch_session_with_records(db, session_id)

        if not session:
            return {"error": f"Session {session_id} not found"}

        # Calculate batch statistics
        total_batches = len(session.batch_records)
        completed_batches = sum(
            1 for r in session.batch_records if r.status == "COMPLETED"
        )
        failed_batches = sum(1 for r in session.batch_records if r.status == "FAILED")
        processing_batches = sum(
            1 for r in session.batch_records if r.status == "PROCESSING"
        )
        pending_batches = sum(1 for r in session.batch_records if r.status == "PENDING")

        # Calculate article statistics
        total_articles_processed = sum(
            r.articles_processed or 0 for r in session.batch_records
        )
        total_articles_failed = sum(
            r.articles_failed or 0 for r in session.batch_records
        )

        # Calculate progress percentage
        completion_percentage = (
            (completed_batches / total_batches * 100) if total_batches > 0 else 0
        )

        # Calculate costs
        actual_cost = session.actual_cost or 0.0
        estimated_cost = session.estimated_cost

        # Calculate timing
        elapsed_time = None
        estimated_completion = None

        if session.started_at:
            elapsed_time = (datetime.utcnow() - session.started_at).total_seconds()

            if completed_batches > 0:
                avg_time_per_batch = elapsed_time / completed_batches
                remaining_batches = total_batches - completed_batches
                estimated_remaining_time = remaining_batches * avg_time_per_batch
                estimated_completion = datetime.utcnow() + timedelta(
                    seconds=estimated_remaining_time
                )

        return {
            "session_id": session_id,
            "status": session.status,
            "progress": {
                "total_articles": session.total_articles,
                "articles_processed": total_articles_processed,
                "articles_failed": total_articles_failed,
                "articles_remaining": session.total_articles
                - total_articles_processed
                - total_articles_failed,
                "completion_percentage": round(completion_percentage, 1),
            },
            "batches": {
                "total_batches": total_batches,
                "completed_batches": completed_batches,
                "failed_batches": failed_batches,
                "processing_batches": processing_batches,
                "pending_batches": pending_batches,
            },
            "costs": {
                "estimated_total": estimated_cost,
                "actual_spent": actual_cost,
                "remaining_budget": BatchProcessingConfig.MAX_TOTAL_BUDGET
                - actual_cost,
                "budget_utilization": (
                    actual_cost / BatchProcessingConfig.MAX_TOTAL_BUDGET * 100
                )
                if actual_cost > 0
                else 0,
            },
            "timing": {
                "started_at": session.started_at.isoformat()
                if session.started_at
                else None,
                "elapsed_seconds": elapsed_time,
                "estimated_completion": estimated_completion.isoformat()
                if estimated_completion
                else None,
            },
        }

    except Exception as e:
        logger.error(f"Failed to calculate session progress: {e}")
        return {"error": str(e)}


async def check_session_alerts(session_status: dict[str, Any]) -> list[dict[str, Any]]:
    """Check for alerts based on session status."""
    alerts = []

    try:
        # Budget alerts
        budget_utilization = session_status.get("costs", {}).get(
            "budget_utilization", 0
        )

        if budget_utilization > 90:
            alerts.append(
                {
                    "type": "budget_critical",
                    "severity": "high",
                    "message": f"Budget utilization at {budget_utilization:.1f}%",
                    "session_id": session_status["session_id"],
                }
            )
        elif budget_utilization > 75:
            alerts.append(
                {
                    "type": "budget_warning",
                    "severity": "medium",
                    "message": f"Budget utilization at {budget_utilization:.1f}%",
                    "session_id": session_status["session_id"],
                }
            )

        # Failure rate alerts
        batches = session_status.get("batches", {})
        total_completed = batches.get("completed_batches", 0) + batches.get(
            "failed_batches", 0
        )

        if total_completed > 0:
            failure_rate = (batches.get("failed_batches", 0) / total_completed) * 100

            if failure_rate > 20:
                alerts.append(
                    {
                        "type": "high_failure_rate",
                        "severity": "high",
                        "message": f"Batch failure rate at {failure_rate:.1f}%",
                        "session_id": session_status["session_id"],
                    }
                )

        # Stalled processing alerts
        processing_batches = batches.get("processing_batches", 0)
        elapsed_seconds = session_status.get("timing", {}).get("elapsed_seconds", 0)

        if processing_batches > 0 and elapsed_seconds > 1800:  # 30 minutes
            alerts.append(
                {
                    "type": "stalled_processing",
                    "severity": "medium",
                    "message": f"Processing stalled for {elapsed_seconds/60:.1f} minutes",
                    "session_id": session_status["session_id"],
                }
            )

    except Exception as e:
        logger.error(f"Failed to check session alerts: {e}")
        alerts.append(
            {
                "type": "monitoring_error",
                "severity": "low",
                "message": f"Alert checking failed: {str(e)}",
                "session_id": session_status.get("session_id", "unknown"),
            }
        )

    return alerts


async def handle_session_issues(
    db, session, session_status: dict[str, Any]
) -> list[dict[str, Any]]:
    """Handle issues found in session monitoring."""
    actions = []

    try:
        storage = BatchStorageManager()

        # Check if session should be finalized
        batches = session_status.get("batches", {})
        total_batches = batches.get("total_batches", 0)
        completed_failed = batches.get("completed_batches", 0) + batches.get(
            "failed_batches", 0
        )

        if total_batches > 0 and completed_failed >= total_batches:
            # All batches are done, finalize session
            await storage.finalize_batch_session(db, session.session_id)
            actions.append(
                {
                    "action": "finalize_session",
                    "session_id": session.session_id,
                    "message": "Session finalized - all batches completed",
                }
            )

        # Check for budget exceeded
        budget_utilization = session_status.get("costs", {}).get(
            "budget_utilization", 0
        )
        if budget_utilization > 100:
            # Cancel remaining batches
            actions.append(
                {
                    "action": "budget_exceeded",
                    "session_id": session.session_id,
                    "message": "Budget exceeded - monitoring flagged for review",
                }
            )

    except Exception as e:
        logger.error(f"Failed to handle session issues: {e}")
        actions.append(
            {
                "action": "error_handling",
                "session_id": session.session_id,
                "error": str(e),
            }
        )

    return actions


async def update_monitoring_metrics(db, monitoring_results: dict[str, Any]) -> None:
    """Update monitoring metrics in database."""
    try:
        # This would store monitoring metrics in a dedicated table
        # For now, just log the results
        logger.info(f"Monitoring metrics: {monitoring_results}")

    except Exception as e:
        logger.error(f"Failed to update monitoring metrics: {e}")


def get_batch_processing_status(session_id: str) -> dict[str, Any]:
    """Get detailed status of batch processing session (sync wrapper)."""

    async def _get_status():
        async with get_db_session() as db:
            return await calculate_session_progress(db, session_id)

    return asyncio.run(_get_status())
