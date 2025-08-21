"""Admin endpoints for task management and system administration."""

from datetime import UTC, datetime
from typing import Any

from crypto_newsletter.core.storage.repository import (
    ArticleRepository,
    NewsletterRepository,
)
from crypto_newsletter.newsletter.monitoring import get_newsletter_health_status
from crypto_newsletter.newsletter.services.progress_tracker import ProgressTracker
from crypto_newsletter.newsletter.tasks import (
    generate_newsletter_manual_task_enhanced,
)
from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.web.models import (
    ManualIngestRequest,
    NewsletterGenerationRequest,
    NewsletterResponse,
    TaskScheduleRequest,
    TaskStatusResponse,
)
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/status")
async def admin_status() -> dict[str, Any]:
    """
    Get overall system status for admin dashboard.

    Returns:
        System status and statistics
    """
    try:
        settings = get_settings()

        # Get database statistics
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            stats = await repo.get_article_statistics()

        # Add status field to database stats
        database_status = {
            "status": "healthy",  # Always healthy if we can connect
            **stats,
        }

        # Initialize Celery status
        celery_status = {
            "enabled": settings.enable_celery,
            "status": "unknown",  # Default status
        }

        # Add Celery status if enabled
        if settings.enable_celery:
            try:
                from crypto_newsletter.core.scheduling.tasks import get_active_tasks
                from crypto_newsletter.shared.celery.worker import get_worker_health

                worker_health = await get_worker_health()
                active_tasks = get_active_tasks()

                # Determine Celery health status
                if worker_health and worker_health.get("status") == "healthy":
                    celery_status["status"] = "healthy"
                elif worker_health and "error" in worker_health:
                    celery_status["status"] = "error"
                else:
                    celery_status["status"] = "warning"

                celery_status.update(
                    {
                        "workers": worker_health,
                        "active_tasks": active_tasks,
                    }
                )
            except Exception as e:
                celery_status.update({"status": "error", "error": str(e)})
        else:
            celery_status["status"] = "warning"  # Not enabled

        # Add newsletter system status
        newsletter_status = {"status": "unknown"}
        try:
            newsletter_health = await get_newsletter_health_status()
            newsletter_status = {
                "status": newsletter_health["overall_status"],
                "generation_metrics": newsletter_health["checks"][
                    "newsletter_generation"
                ]["metrics"],
                "pipeline_metrics": newsletter_health["checks"]["newsletter_pipeline"][
                    "metrics"
                ],
                "issues": newsletter_health["checks"]["newsletter_generation"].get(
                    "issues", []
                ),
            }
        except Exception as e:
            newsletter_status = {"status": "error", "error": str(e)}

        # Add API status
        api_status = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": "running",
            "environment": settings.railway_environment,
        }

        status = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "crypto-newsletter",
            "environment": settings.railway_environment,
            "api": api_status,
            "database": database_status,
            "celery": celery_status,
            "newsletter": newsletter_status,
        }

        return status

    except Exception as e:
        # If we can't connect to database, mark it as error
        env = "unknown"
        if "settings" in locals():
            env = settings.railway_environment

        api_status = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": "running",
            "environment": env,
        }

        database_status = {"status": "error", "error": str(e)}

        celery_status = {"enabled": False, "status": "unknown"}

        newsletter_status = {"status": "unknown", "error": "Database connection failed"}

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "crypto-newsletter",
            "environment": env,
            "api": api_status,
            "database": database_status,
            "celery": celery_status,
            "newsletter": newsletter_status,
        }


@router.post("/tasks/schedule-ingest")
async def schedule_ingestion_task(request: TaskScheduleRequest) -> dict[str, Any]:
    """
    Schedule an immediate article ingestion task.

    Args:
        request: Task scheduling parameters

    Returns:
        Task scheduling result with task ID
    """
    settings = get_settings()

    if not settings.enable_celery:
        raise HTTPException(
            status_code=503, detail="Celery is not enabled. Cannot schedule tasks."
        )

    try:
        from crypto_newsletter.core.scheduling.tasks import manual_ingest

        # Schedule the task
        result = manual_ingest.delay(
            limit=request.limit,
            hours_back=request.hours_back,
            categories=request.categories,
        )

        return {
            "success": True,
            "task_id": result.id,
            "status": result.status,
            "message": "Ingestion task scheduled successfully",
            "parameters": {
                "limit": request.limit,
                "hours_back": request.hours_back,
                "categories": request.categories,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to schedule ingestion task: {e}"
        )


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get status of a specific task.

    Args:
        task_id: ID of the task to check

    Returns:
        Task status information
    """
    settings = get_settings()

    if not settings.enable_celery:
        raise HTTPException(
            status_code=503, detail="Celery is not enabled. Cannot check task status."
        )

    try:
        from crypto_newsletter.core.scheduling.tasks import get_task_status

        status = get_task_status(task_id)

        return TaskStatusResponse(
            task_id=status["task_id"],
            status=status["status"],
            result=status["result"],
            date_done=status["date_done"],
            traceback=status["traceback"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {e}")


@router.get("/tasks/active")
async def get_active_tasks() -> dict[str, Any]:
    """
    Get information about currently active tasks.

    Returns:
        Active task information
    """
    settings = get_settings()

    if not settings.enable_celery:
        raise HTTPException(
            status_code=503, detail="Celery is not enabled. Cannot get active tasks."
        )

    try:
        from crypto_newsletter.core.scheduling.tasks import get_active_tasks

        active_tasks = get_active_tasks()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "active_tasks": active_tasks,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active tasks: {e}")


@router.post("/ingest")
async def manual_ingest(request: ManualIngestRequest) -> dict[str, Any]:
    """
    Trigger manual article ingestion (synchronous).

    Args:
        request: Ingestion parameters

    Returns:
        Ingestion results
    """
    try:
        from crypto_newsletter.core.ingestion.pipeline import ArticleIngestionPipeline

        # Run ingestion pipeline directly
        pipeline = ArticleIngestionPipeline()
        results = await pipeline.run_full_ingestion(
            limit=request.limit,
            hours_back=request.hours_back,
            categories=request.categories,
        )

        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now(UTC).isoformat(),
            "parameters": {
                "limit": request.limit,
                "hours_back": request.hours_back,
                "categories": request.categories,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual ingestion failed: {e}")


@router.post("/batch-processing/initiate")
async def initiate_batch_processing(force_processing: bool = False) -> dict[str, Any]:
    """
    Initiate batch processing of unanalyzed articles.

    Args:
        force_processing: Process even if budget constraints exist

    Returns:
        Batch processing initiation result
    """
    settings = get_settings()

    if not settings.enable_celery:
        raise HTTPException(
            status_code=503,
            detail="Celery is not enabled. Cannot initiate batch processing.",
        )

    try:
        from crypto_newsletter.newsletter.batch.tasks import initiate_batch_processing

        # Schedule the batch processing task
        result = initiate_batch_processing.delay(force_processing=force_processing)

        return {
            "success": True,
            "task_id": result.id,
            "status": result.status,
            "message": "Batch processing initiated successfully",
            "parameters": {
                "force_processing": force_processing,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate batch processing: {e}"
        )


@router.get("/stats")
async def get_system_stats() -> dict[str, Any]:
    """
    Get comprehensive system statistics.

    Returns:
        System statistics and metrics
    """
    try:
        # Get database statistics
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            stats = await repo.get_article_statistics()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "crypto-newsletter",
            "environment": get_settings().railway_environment,
            "statistics": stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system statistics: {e}"
        )


@router.post("/newsletter/generate")
async def generate_newsletter(force_generation: bool = False) -> dict[str, Any]:
    """
    Generate a newsletter from analyzed articles.

    Args:
        force_generation: Generate even if insufficient analyzed articles

    Returns:
        Newsletter generation result
    """
    try:
        from crypto_newsletter.newsletter.agents.orchestrator import (
            newsletter_orchestrator,
        )
        from crypto_newsletter.shared.database.connection import get_db_session
        from sqlalchemy import text

        # Get analyzed articles from the last 24 hours
        async with get_db_session() as db:
            query = text(
                """
                SELECT
                    a.id,
                    a.title,
                    p.name as publisher,
                    a.published_on,
                    a.body,
                    aa.signal_strength,
                    aa.uniqueness_score,
                    aa.analysis_confidence,
                    aa.weak_signals,
                    aa.pattern_anomalies,
                    aa.adjacent_connections
                FROM articles a
                JOIN publishers p ON a.publisher_id = p.id
                JOIN article_analyses aa ON a.id = aa.article_id
                WHERE aa.created_at >= NOW() - INTERVAL '24 hours'
                  AND LENGTH(a.body) > 2000
                  AND aa.signal_strength > 0.6
                ORDER BY aa.signal_strength DESC
                LIMIT 10
            """
            )

            result = await db.execute(query)
            articles = []

            for row in result.fetchall():
                articles.append(
                    {
                        "id": row[0],
                        "title": row[1],
                        "publisher": row[2],
                        "published_on": row[3].isoformat() if row[3] else None,
                        "body": row[4],
                        "signal_strength": float(row[5]) if row[5] else 0.0,
                        "uniqueness_score": float(row[6]) if row[6] else 0.0,
                        "analysis_confidence": float(row[7]) if row[7] else 0.0,
                        "weak_signals": row[8] if row[8] else [],
                        "pattern_anomalies": row[9] if row[9] else [],
                        "adjacent_connections": row[10] if row[10] else [],
                    }
                )

        if len(articles) < 3 and not force_generation:
            return {
                "success": False,
                "error": "Insufficient analyzed articles for newsletter generation",
                "articles_found": len(articles),
                "minimum_required": 3,
                "suggestion": "Use force_generation=true to proceed anyway",
            }

        # Generate newsletter using orchestrator
        newsletter_result = await newsletter_orchestrator.generate_daily_newsletter(
            articles
        )

        return {
            "success": True,
            "newsletter_result": newsletter_result,
            "articles_processed": len(articles),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate newsletter: {e}"
        )


# Newsletter Management Endpoints
@router.post("/newsletters/generate")
async def admin_generate_newsletter(
    request: NewsletterGenerationRequest,
) -> dict[str, Any]:
    """
    Admin endpoint to manually trigger newsletter generation.

    Args:
        request: Newsletter generation parameters

    Returns:
        Generation task information and status
    """
    settings = get_settings()

    if not settings.enable_celery:
        raise HTTPException(
            status_code=503,
            detail="Celery is not enabled. Cannot generate newsletters.",
        )

    try:
        # Validate newsletter type
        if request.newsletter_type.upper() not in ["DAILY", "WEEKLY"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid newsletter type: {request.newsletter_type}. Must be DAILY or WEEKLY",
            )

        # Trigger enhanced newsletter generation task with progress tracking
        result = generate_newsletter_manual_task_enhanced.delay(
            newsletter_type=request.newsletter_type.upper(),
            force_generation=request.force_generation,
        )

        return {
            "success": True,
            "task_id": result.id,
            "newsletter_type": request.newsletter_type.upper(),
            "force_generation": request.force_generation,
            "status": "queued",
            "message": f"{request.newsletter_type.upper()} newsletter generation started with progress tracking",
            "progress_endpoint": f"/admin/tasks/{result.id}/progress",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger newsletter generation: {e}"
        )


@router.get("/newsletters/stats")
async def get_newsletter_stats() -> dict[str, Any]:
    """
    Get newsletter generation statistics for admin dashboard.

    Returns:
        Newsletter statistics and metrics
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            # Get recent newsletters (past 30 days)
            from datetime import timedelta

            end_date = datetime.now(UTC).date()
            start_date = end_date - timedelta(days=30)

            recent_newsletters = await newsletter_repo.get_newsletters_with_filters(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=100,
            )

            # Calculate statistics
            total_newsletters = len(recent_newsletters)
            daily_newsletters = [
                n
                for n in recent_newsletters
                if n.generation_metadata
                and n.generation_metadata.get("newsletter_type") == "DAILY"
            ]
            weekly_newsletters = [
                n
                for n in recent_newsletters
                if n.generation_metadata
                and n.generation_metadata.get("newsletter_type") == "WEEKLY"
            ]

            # Status breakdown
            status_counts = {}
            for newsletter in recent_newsletters:
                status = newsletter.status
                status_counts[status] = status_counts.get(status, 0) + 1

            # Quality metrics
            quality_scores = [
                n.quality_score for n in recent_newsletters if n.quality_score
            ]
            avg_quality = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            )

            # Generation costs
            generation_costs = []
            for newsletter in recent_newsletters:
                if newsletter.generation_metadata:
                    cost = newsletter.generation_metadata.get("generation_cost", 0.0)
                    if cost:
                        generation_costs.append(cost)

            total_cost = sum(generation_costs)
            avg_cost = total_cost / len(generation_costs) if generation_costs else 0.0

            return {
                "period": "past_30_days",
                "total_newsletters": total_newsletters,
                "newsletter_types": {
                    "daily": len(daily_newsletters),
                    "weekly": len(weekly_newsletters),
                },
                "status_breakdown": status_counts,
                "quality_metrics": {
                    "average_quality_score": round(avg_quality, 3),
                    "newsletters_with_scores": len(quality_scores),
                },
                "cost_metrics": {
                    "total_generation_cost": round(total_cost, 4),
                    "average_cost_per_newsletter": round(avg_cost, 4),
                    "newsletters_with_cost_data": len(generation_costs),
                },
                "recent_newsletters": [
                    {
                        "id": n.id,
                        "title": n.title,
                        "type": n.generation_metadata.get("newsletter_type", "UNKNOWN")
                        if n.generation_metadata
                        else "UNKNOWN",
                        "status": n.status,
                        "generation_date": n.generation_date.isoformat(),
                        "quality_score": n.quality_score,
                    }
                    for n in recent_newsletters[:10]  # Last 10 newsletters
                ],
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve newsletter statistics: {e}"
        )


@router.get("/newsletters")
async def get_admin_newsletters(
    limit: int = 20, status: str = None, newsletter_type: str = None
) -> dict[str, Any]:
    """
    Get newsletters for admin dashboard with filtering.

    Args:
        limit: Maximum number of newsletters to return
        status: Filter by newsletter status
        newsletter_type: Filter by newsletter type (DAILY/WEEKLY)

    Returns:
        List of newsletters with admin metadata
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            newsletters = await newsletter_repo.get_newsletters_with_filters(
                limit=limit, status=status, newsletter_type=newsletter_type
            )

            # Convert to admin response format
            newsletter_list = []
            for newsletter in newsletters:
                newsletter_data = {
                    "id": newsletter.id,
                    "title": newsletter.title,
                    "status": newsletter.status,
                    "generation_date": newsletter.generation_date.isoformat(),
                    "quality_score": newsletter.quality_score,
                    "agent_version": newsletter.agent_version,
                    "created_at": newsletter.created_at.isoformat(),
                    "updated_at": newsletter.updated_at.isoformat(),
                }

                # Add generation metadata if available
                if newsletter.generation_metadata:
                    newsletter_data.update(
                        {
                            "newsletter_type": newsletter.generation_metadata.get(
                                "newsletter_type", "UNKNOWN"
                            ),
                            "generation_cost": newsletter.generation_metadata.get(
                                "generation_cost", 0.0
                            ),
                            "processing_time": newsletter.generation_metadata.get(
                                "processing_time_seconds", 0.0
                            ),
                            "articles_processed": newsletter.generation_metadata.get(
                                "articles_processed", 0
                            ),
                        }
                    )

                newsletter_list.append(newsletter_data)

            return {
                "newsletters": newsletter_list,
                "count": len(newsletter_list),
                "filters_applied": {
                    "limit": limit,
                    "status": status,
                    "newsletter_type": newsletter_type,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve newsletters: {e}"
        )


@router.get("/newsletters/{newsletter_id}")
async def get_admin_newsletter_detail(newsletter_id: int) -> NewsletterResponse:
    """
    Get detailed newsletter information for admin dashboard.

    Args:
        newsletter_id: Newsletter ID to retrieve

    Returns:
        Complete newsletter details with admin metadata
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            newsletter = await newsletter_repo.get_newsletter_by_id(
                newsletter_id, include_articles=True
            )
            if not newsletter:
                raise HTTPException(
                    status_code=404,
                    detail=f"Newsletter with ID {newsletter_id} not found",
                )

            return NewsletterResponse(
                id=newsletter.id,
                title=newsletter.title,
                content=newsletter.content,
                summary=newsletter.summary,
                generation_date=newsletter.generation_date.isoformat(),
                status=newsletter.status,
                quality_score=newsletter.quality_score,
                agent_version=newsletter.agent_version,
                generation_metadata=newsletter.generation_metadata,
                published_at=newsletter.published_at.isoformat()
                if newsletter.published_at
                else None,
                created_at=newsletter.created_at.isoformat(),
                updated_at=newsletter.updated_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve newsletter details: {e}"
        )


@router.put("/newsletters/{newsletter_id}/status")
async def update_admin_newsletter_status(
    newsletter_id: int, status: str, title: str = None, summary: str = None
) -> dict[str, Any]:
    """
    Admin endpoint to update newsletter status and metadata.

    Args:
        newsletter_id: Newsletter ID to update
        status: New newsletter status (DRAFT, REVIEW, PUBLISHED, ARCHIVED)
        title: Optional new title
        summary: Optional new summary

    Returns:
        Update confirmation with newsletter details
    """
    try:
        # Validate status
        valid_statuses = ["DRAFT", "REVIEW", "PUBLISHED", "ARCHIVED"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of {valid_statuses}",
            )

        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            # Check if newsletter exists
            newsletter = await newsletter_repo.get_newsletter_by_id(newsletter_id)
            if not newsletter:
                raise HTTPException(
                    status_code=404,
                    detail=f"Newsletter with ID {newsletter_id} not found",
                )

            # Update newsletter
            updated_newsletter = await newsletter_repo.update_newsletter(
                newsletter_id=newsletter_id,
                status=status,
                title=title,
                summary=summary,
            )

            return {
                "success": True,
                "newsletter_id": newsletter_id,
                "previous_status": newsletter.status,
                "new_status": status,
                "updated_fields": {
                    k: v
                    for k, v in {
                        "status": status,
                        "title": title,
                        "summary": summary,
                    }.items()
                    if v is not None
                },
                "published_at": updated_newsletter.published_at.isoformat()
                if updated_newsletter.published_at
                else None,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update newsletter status: {e}"
        )


@router.delete("/newsletters/{newsletter_id}")
async def delete_admin_newsletter(newsletter_id: int) -> dict[str, Any]:
    """
    Admin endpoint to delete newsletter.

    Args:
        newsletter_id: Newsletter ID to delete

    Returns:
        Deletion confirmation
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            # Check if newsletter exists
            newsletter = await newsletter_repo.get_newsletter_by_id(newsletter_id)
            if not newsletter:
                raise HTTPException(
                    status_code=404,
                    detail=f"Newsletter with ID {newsletter_id} not found",
                )

            # Store newsletter info before deletion
            newsletter_info = {
                "id": newsletter.id,
                "title": newsletter.title,
                "status": newsletter.status,
                "generation_date": newsletter.generation_date.isoformat(),
                "newsletter_type": newsletter.generation_metadata.get(
                    "newsletter_type", "UNKNOWN"
                )
                if newsletter.generation_metadata
                else "UNKNOWN",
            }

            # Delete newsletter
            success = await newsletter_repo.delete_newsletter(newsletter_id)

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to delete newsletter"
                )

            return {
                "success": True,
                "deleted_newsletter": newsletter_info,
                "message": f"Newsletter '{newsletter.title}' deleted successfully",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete newsletter: {e}")


@router.get("/tasks/{task_id}/progress")
async def get_generation_progress(task_id: str) -> dict[str, Any]:
    """Get real-time progress for newsletter generation task."""
    try:
        async with ProgressTracker() as tracker:
            progress = await tracker.get_progress(task_id)

            if not progress:
                raise HTTPException(status_code=404, detail="Task not found")

            return {
                "task_id": task_id,
                "current_step": progress.current_step,
                "step_progress": progress.step_progress,
                "overall_progress": progress.overall_progress,
                "status": progress.status,
                "step_details": progress.step_details,
                "intermediate_results": progress.intermediate_results,
                "estimated_completion": (
                    progress.estimated_completion.isoformat()
                    if progress.estimated_completion
                    else None
                ),
                "created_at": progress.created_at.isoformat(),
                "updated_at": progress.updated_at.isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get progress for task {task_id}: {e}"
        )
