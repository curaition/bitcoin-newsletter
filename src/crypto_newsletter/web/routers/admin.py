"""Admin endpoints for task management and system administration."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from crypto_newsletter.core.storage.repository import ArticleRepository
from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.web.models import (
    ManualIngestRequest,
    TaskScheduleRequest,
    TaskStatusResponse,
)

router = APIRouter()


@router.get("/status")
async def admin_status() -> Dict[str, Any]:
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
        
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "crypto-newsletter",
            "environment": settings.railway_environment,
            "database": stats,
            "celery": {"enabled": settings.enable_celery},
        }
        
        # Add Celery status if enabled
        if settings.enable_celery:
            try:
                from crypto_newsletter.core.scheduling.tasks import get_active_tasks
                from crypto_newsletter.shared.celery.worker import get_worker_health
                
                worker_health = await get_worker_health()
                active_tasks = get_active_tasks()
                
                status["celery"].update({
                    "workers": worker_health,
                    "active_tasks": active_tasks,
                })
            except Exception as e:
                status["celery"]["error"] = str(e)
        
        return status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get admin status: {e}"
        )


@router.post("/tasks/schedule-ingest")
async def schedule_ingestion_task(request: TaskScheduleRequest) -> Dict[str, Any]:
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
            status_code=503,
            detail="Celery is not enabled. Cannot schedule tasks."
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule ingestion task: {e}"
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
            status_code=503,
            detail="Celery is not enabled. Cannot check task status."
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {e}"
        )


@router.get("/tasks/active")
async def get_active_tasks() -> Dict[str, Any]:
    """
    Get information about currently active tasks.
    
    Returns:
        Active task information
    """
    settings = get_settings()
    
    if not settings.enable_celery:
        raise HTTPException(
            status_code=503,
            detail="Celery is not enabled. Cannot get active tasks."
        )
    
    try:
        from crypto_newsletter.core.scheduling.tasks import get_active_tasks
        
        active_tasks = get_active_tasks()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_tasks": active_tasks,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active tasks: {e}"
        )


@router.post("/ingest")
async def manual_ingest(request: ManualIngestRequest) -> Dict[str, Any]:
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "parameters": {
                "limit": request.limit,
                "hours_back": request.hours_back,
                "categories": request.categories,
            },
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Manual ingestion failed: {e}"
        )


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "crypto-newsletter",
            "environment": get_settings().railway_environment,
            "statistics": stats,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system statistics: {e}"
        )
