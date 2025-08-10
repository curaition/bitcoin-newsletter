"""Health check endpoints for monitoring and Railway deployment."""

import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlalchemy import text

from crypto_newsletter.core.ingestion import pipeline_health_check
from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session

router = APIRouter()


@router.get("/")
async def basic_health() -> Dict[str, Any]:
    """
    Basic health check for Railway and load balancers.
    
    Returns:
        Simple health status for quick checks
    """
    return {
        "status": "healthy",
        "service": "crypto-newsletter",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.
    
    Returns:
        Service readiness status
        
    Raises:
        HTTPException: If service is not ready
    """
    try:
        # Quick database check
        async with get_db_session() as db:
            await db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "service": "crypto-newsletter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.
    
    Returns:
        Service liveness status
    """
    return {
        "status": "alive",
        "service": "crypto-newsletter",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "running",  # Could add actual uptime calculation
    }


@router.get("/detailed")
async def detailed_health() -> Dict[str, Any]:
    """
    Comprehensive health check with all system components.
    
    Returns:
        Detailed health status for all components
        
    Raises:
        HTTPException: If critical components are unhealthy
    """
    settings = get_settings()
    
    try:
        # Run comprehensive health check
        health_result = await pipeline_health_check()
        
        # Add additional system information
        health_result.update({
            "service": "crypto-newsletter",
            "environment": settings.railway_environment,
            "service_type": os.getenv("SERVICE_TYPE", "web"),
            "railway_environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
            "celery_enabled": settings.enable_celery,
        })
        
        # Check Celery workers if enabled
        if settings.enable_celery:
            try:
                from crypto_newsletter.shared.celery.worker import get_worker_health, get_queue_health
                
                worker_health = await get_worker_health()
                queue_health = await get_queue_health()
                
                health_result["checks"]["celery_workers"] = worker_health
                health_result["checks"]["celery_queues"] = queue_health
                
                # Update overall status if Celery is unhealthy
                if worker_health["status"] != "healthy":
                    health_result["status"] = "degraded"
                    
            except Exception as e:
                health_result["checks"]["celery"] = {
                    "status": "unhealthy",
                    "message": f"Celery check failed: {e}",
                }
                health_result["status"] = "degraded"
        
        # Determine HTTP status code
        if health_result["status"] == "healthy":
            return health_result
        elif health_result["status"] == "degraded":
            # Return 200 but indicate degraded performance
            return health_result
        else:
            # Return 503 for unhealthy status
            raise HTTPException(
                status_code=503,
                detail=health_result
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Health check failed with unexpected error: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": "Health check failed",
                "detail": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


@router.get("/metrics")
async def metrics_endpoint() -> Dict[str, Any]:
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        System metrics and statistics
    """
    try:
        from crypto_newsletter.core.storage.repository import ArticleRepository
        
        # Get database statistics
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            stats = await repo.get_statistics()
        
        # Add system metrics
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "crypto-newsletter",
            "database": {
                "total_articles": stats.get("total_articles", 0),
                "recent_articles": stats.get("recent_articles", 0),
                "total_publishers": stats.get("total_publishers", 0),
                "total_categories": stats.get("total_categories", 0),
            },
            "system": {
                "environment": get_settings().environment,
                "celery_enabled": get_settings().enable_celery,
            }
        }
        
        # Add Celery metrics if available
        if get_settings().enable_celery:
            try:
                from crypto_newsletter.core.scheduling.tasks import get_active_tasks
                active_tasks = get_active_tasks()
                
                metrics["celery"] = {
                    "active_tasks": len(active_tasks.get("active", {}).get("celery@hostname", [])),
                    "scheduled_tasks": len(active_tasks.get("scheduled", {}).get("celery@hostname", [])),
                }
            except Exception:
                metrics["celery"] = {"status": "unavailable"}
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Metrics collection failed",
                "detail": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
