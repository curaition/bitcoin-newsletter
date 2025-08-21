"""Health check endpoints for monitoring and Railway deployment."""

import os
from datetime import UTC, datetime
from typing import Any

from crypto_newsletter.core.ingestion import pipeline_health_check
from crypto_newsletter.newsletter.monitoring import get_newsletter_health_status
from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.logging.config import get_logger
from crypto_newsletter.shared.monitoring.metrics import (
    get_metrics_collector,
)
from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlalchemy import text

router = APIRouter()


@router.get("/")
async def basic_health() -> dict[str, Any]:
    """
    Basic health check for Railway and load balancers.

    Returns:
        Simple health status for quick checks
    """
    return {
        "status": "healthy",
        "service": "crypto-newsletter",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
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
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )


@router.get("/live")
async def liveness_check() -> dict[str, Any]:
    """
    Kubernetes-style liveness probe.

    Returns:
        Service liveness status
    """
    return {
        "status": "alive",
        "service": "crypto-newsletter",
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime": "running",  # Could add actual uptime calculation
    }


@router.get("/detailed")
async def detailed_health() -> dict[str, Any]:
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

        # Add newsletter system health check
        newsletter_status = await get_newsletter_health_status()
        health_result["checks"]["newsletter_system"] = newsletter_status

        # Update overall status based on newsletter health
        if newsletter_status["overall_status"] == "unhealthy":
            health_result["status"] = "unhealthy"
        elif (
            newsletter_status["overall_status"] == "warning"
            and health_result["status"] == "healthy"
        ):
            health_result["status"] = "degraded"

        # Add additional system information
        health_result.update(
            {
                "service": "crypto-newsletter",
                "environment": settings.railway_environment,
                "service_type": os.getenv("SERVICE_TYPE", "web"),
                "railway_environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
                "celery_enabled": settings.enable_celery,
            }
        )

        # Check Celery workers if enabled
        if settings.enable_celery:
            try:
                from crypto_newsletter.shared.celery.worker import (
                    get_queue_health,
                    get_worker_health,
                )

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
            raise HTTPException(status_code=503, detail=health_result)

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
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )


@router.get("/metrics")
async def metrics_endpoint() -> dict[str, Any]:
    """
    Enhanced metrics endpoint for comprehensive monitoring.

    Returns:
        System metrics, application metrics, and statistics
    """
    metrics_logger = get_logger("health.metrics")
    collector = get_metrics_collector()

    try:
        # Collect comprehensive metrics using new monitoring system
        system_metrics = collector.collect_system_metrics()
        app_metrics = collector.collect_application_metrics()
        db_metrics = await collector.collect_database_metrics()
        task_metrics = collector.collect_task_metrics()

        # Legacy database statistics for backward compatibility
        from crypto_newsletter.core.storage.repository import ArticleRepository

        async with get_db_session() as db:
            repo = ArticleRepository(db)
            legacy_stats = await repo.get_statistics()

        # Combine all metrics
        metrics = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": "crypto-newsletter",
            "environment": get_settings().railway_environment,
            "system": {
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "memory_used_mb": system_metrics.memory_used_mb,
                "disk_percent": system_metrics.disk_percent,
                "disk_free_gb": system_metrics.disk_free_gb,
                "process_count": system_metrics.process_count,
                "load_average": system_metrics.load_average,
            },
            "application": {
                "uptime_seconds": app_metrics.uptime_seconds,
                "total_requests": app_metrics.total_requests,
                "error_count": app_metrics.error_count,
                "avg_response_time_ms": app_metrics.avg_response_time_ms,
                "cache_hit_rate": app_metrics.cache_hit_rate,
            },
            "database": {
                "total_articles": db_metrics.total_articles,
                "articles_today": db_metrics.articles_today,
                "connection_count": db_metrics.connection_count,
                "active_queries": db_metrics.active_queries,
                # Legacy compatibility
                "total_publishers": legacy_stats.get("total_publishers", 0),
                "total_categories": legacy_stats.get("total_categories", 0),
            },
            "tasks": {
                "active_tasks": task_metrics.active_tasks,
                "pending_tasks": task_metrics.pending_tasks,
                "completed_today": task_metrics.completed_tasks_today,
                "failed_today": task_metrics.failed_tasks_today,
                "queue_lengths": task_metrics.queue_lengths,
            },
        }

        metrics_logger.info(
            "Enhanced metrics collected",
            extra={
                "cpu_percent": system_metrics.cpu_percent,
                "memory_percent": system_metrics.memory_percent,
                "total_requests": app_metrics.total_requests,
                "total_articles": db_metrics.total_articles,
            },
        )

        return metrics

    except Exception as e:
        metrics_logger.error(
            "Enhanced metrics collection failed",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Metrics collection failed",
                "detail": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )


@router.get("/newsletter")
async def newsletter_health() -> dict[str, Any]:
    """
    Newsletter system health check endpoint.

    Returns:
        Newsletter generation status and metrics

    Raises:
        HTTPException: If newsletter system is unhealthy
    """
    try:
        newsletter_status = await get_newsletter_health_status()

        # Determine HTTP status code based on newsletter health
        if newsletter_status["overall_status"] == "healthy":
            return newsletter_status
        elif newsletter_status["overall_status"] == "warning":
            # Return 200 but indicate warnings
            return newsletter_status
        else:
            # Return 503 for unhealthy status
            raise HTTPException(status_code=503, detail=newsletter_status)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Newsletter health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "overall_status": "unhealthy",
                "error": "Newsletter health check failed",
                "detail": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
