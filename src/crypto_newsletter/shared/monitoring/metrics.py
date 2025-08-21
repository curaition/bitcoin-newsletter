"""Metrics collection and monitoring utilities."""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import psutil
from crypto_newsletter.newsletter.models.progress import NewsletterGenerationProgress
from crypto_newsletter.shared.config.settings import get_settings
from loguru import logger


@dataclass
class SystemMetrics:
    """System resource metrics."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    load_average: list[float]
    process_count: int


@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""

    timestamp: str
    service_type: str
    uptime_seconds: float
    active_connections: int
    total_requests: int
    error_count: int
    avg_response_time_ms: float
    cache_hit_rate: float


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""

    timestamp: str
    connection_count: int
    active_queries: int
    total_articles: int
    articles_today: int
    avg_query_time_ms: float
    slow_queries_count: int


@dataclass
class TaskMetrics:
    """Celery task metrics."""

    timestamp: str
    active_tasks: int
    pending_tasks: int
    completed_tasks_today: int
    failed_tasks_today: int
    avg_task_duration_ms: float
    queue_lengths: dict[str, int]


class MetricsCollector:
    """Centralized metrics collection system."""

    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        self._response_times = []
        self._cache_hits = 0
        self._cache_misses = 0

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]  # Windows fallback

            # Process count
            process_count = len(psutil.pids())

            return SystemMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk.percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                load_average=load_avg,
                process_count=process_count,
            )
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                load_average=[0.0, 0.0, 0.0],
                process_count=0,
            )

    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics."""
        uptime = time.time() - self.start_time
        avg_response_time = (
            sum(self._response_times) / len(self._response_times)
            if self._response_times
            else 0.0
        )

        cache_total = self._cache_hits + self._cache_misses
        cache_hit_rate = self._cache_hits / cache_total if cache_total > 0 else 0.0

        return ApplicationMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            service_type=self.settings.service_type,
            uptime_seconds=uptime,
            active_connections=self._get_active_connections(),
            total_requests=self._request_count,
            error_count=self._error_count,
            avg_response_time_ms=avg_response_time,
            cache_hit_rate=cache_hit_rate,
        )

    async def collect_database_metrics(self) -> DatabaseMetrics:
        """Collect database performance metrics."""
        try:
            from crypto_newsletter.core.storage.repository import ArticleRepository
            from crypto_newsletter.shared.database.connection import get_db_session

            async with get_db_session() as db:
                repo = ArticleRepository(db)
                stats = await repo.get_article_statistics()

                # Get connection count (PostgreSQL specific)
                connection_result = await db.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                connection_count = connection_result.scalar() or 0

                # Get active queries count
                active_queries_result = await db.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query != '<IDLE>'"
                )
                active_queries = active_queries_result.scalar() or 0

                return DatabaseMetrics(
                    timestamp=datetime.now(UTC).isoformat(),
                    connection_count=connection_count,
                    active_queries=active_queries,
                    total_articles=stats.get("total_articles", 0),
                    articles_today=stats.get("recent_articles_24h", 0),
                    avg_query_time_ms=0.0,  # Would need query performance tracking
                    slow_queries_count=0,  # Would need slow query log analysis
                )
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return DatabaseMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                connection_count=0,
                active_queries=0,
                total_articles=0,
                articles_today=0,
                avg_query_time_ms=0.0,
                slow_queries_count=0,
            )

    def collect_task_metrics(self) -> TaskMetrics:
        """Collect Celery task metrics."""
        try:
            from crypto_newsletter.core.scheduling.tasks import get_active_tasks

            task_info = get_active_tasks()

            # Count active tasks across all workers
            active_count = sum(
                len(tasks) for tasks in task_info.get("active", {}).values()
            )

            # Get queue lengths (would need Redis inspection)
            queue_lengths = self._get_queue_lengths()

            return TaskMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                active_tasks=active_count,
                pending_tasks=sum(queue_lengths.values()),
                completed_tasks_today=0,  # Would need task result tracking
                failed_tasks_today=0,  # Would need task result tracking
                avg_task_duration_ms=0.0,  # Would need task timing tracking
                queue_lengths=queue_lengths,
            )
        except Exception as e:
            logger.error(f"Failed to collect task metrics: {e}")
            return TaskMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                active_tasks=0,
                pending_tasks=0,
                completed_tasks_today=0,
                failed_tasks_today=0,
                avg_task_duration_ms=0.0,
                queue_lengths={},
            )

    def record_request(self, response_time_ms: float, status_code: int):
        """Record HTTP request metrics."""
        self._request_count += 1
        self._response_times.append(response_time_ms)

        # Keep only last 1000 response times for memory efficiency
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]

        if status_code >= 400:
            self._error_count += 1

        logger.debug(
            "Request recorded",
            extra={
                "response_time_ms": response_time_ms,
                "status_code": status_code,
                "total_requests": self._request_count,
            },
        )

    def record_cache_hit(self):
        """Record cache hit."""
        self._cache_hits += 1

    def record_cache_miss(self):
        """Record cache miss."""
        self._cache_misses += 1

    def _get_active_connections(self) -> int:
        """Get number of active connections."""
        try:
            # This would depend on the web server implementation
            # For now, return a placeholder
            return 0
        except Exception:
            return 0

    def _get_queue_lengths(self) -> dict[str, int]:
        """Get Celery queue lengths."""
        try:
            import redis

            r = redis.from_url(self.settings.redis_url)

            queues = ["default", "ingestion", "monitoring", "maintenance"]
            queue_lengths = {}

            for queue in queues:
                length = r.llen(f"celery:{queue}")
                queue_lengths[queue] = length

            return queue_lengths
        except Exception as e:
            logger.error(f"Failed to get queue lengths: {e}")
            return {}

    async def collect_newsletter_generation_metrics(self) -> dict[str, Any]:
        """Collect newsletter generation progress and quality metrics."""
        try:
            from crypto_newsletter.shared.database.connection import get_db_session
            from sqlalchemy import select

            async with get_db_session() as db:
                # Get recent generation progress (use naive datetime for database query)
                cutoff_time = datetime.now() - timedelta(hours=24)
                recent_progress_query = (
                    select(NewsletterGenerationProgress)
                    .where(NewsletterGenerationProgress.created_at >= cutoff_time)
                    .order_by(NewsletterGenerationProgress.created_at.desc())
                    .limit(10)
                )

                result = await db.execute(recent_progress_query)
                recent_generations = result.scalars().all()

                # Calculate metrics
                total_generations = len(recent_generations)
                successful_generations = len(
                    [g for g in recent_generations if g.status == "complete"]
                )
                failed_generations = len(
                    [g for g in recent_generations if g.status == "failed"]
                )
                in_progress_generations = len(
                    [g for g in recent_generations if g.status == "in_progress"]
                )

                # Calculate average quality scores
                completed_generations = [
                    g for g in recent_generations if g.status == "complete"
                ]
                avg_quality_score = 0.0
                avg_citation_count = 0
                avg_word_count = 0

                if completed_generations:
                    quality_scores = []
                    citation_counts = []
                    word_counts = []

                    for gen in completed_generations:
                        if gen.step_details:
                            if "final_quality_score" in gen.step_details:
                                quality_scores.append(
                                    gen.step_details["final_quality_score"]
                                )
                            if "citation_count" in gen.step_details:
                                citation_counts.append(
                                    gen.step_details["citation_count"]
                                )
                            if "word_count" in gen.step_details:
                                word_counts.append(gen.step_details["word_count"])

                    avg_quality_score = (
                        sum(quality_scores) / len(quality_scores)
                        if quality_scores
                        else 0.0
                    )
                    avg_citation_count = (
                        sum(citation_counts) / len(citation_counts)
                        if citation_counts
                        else 0
                    )
                    avg_word_count = (
                        sum(word_counts) / len(word_counts) if word_counts else 0
                    )

                return {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "total_generations_24h": total_generations,
                    "successful_generations": successful_generations,
                    "failed_generations": failed_generations,
                    "in_progress_generations": in_progress_generations,
                    "success_rate": successful_generations / total_generations
                    if total_generations > 0
                    else 0.0,
                    "failure_rate": failed_generations / total_generations
                    if total_generations > 0
                    else 0.0,
                    "avg_quality_score": avg_quality_score,
                    "avg_citation_count": avg_citation_count,
                    "avg_word_count": avg_word_count,
                    "quality_alerts": self._check_quality_alerts(
                        avg_quality_score,
                        avg_citation_count,
                        failed_generations,
                        total_generations,
                    ),
                }

        except Exception as e:
            logger.error(f"Failed to collect newsletter generation metrics: {e}")
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "error": str(e),
                "total_generations_24h": 0,
                "successful_generations": 0,
                "failed_generations": 0,
                "quality_alerts": [],
            }

    def _check_quality_alerts(
        self,
        avg_quality_score: float,
        avg_citation_count: int,
        failed_generations: int,
        total_generations: int,
    ) -> list[dict[str, Any]]:
        """Check for quality-related alerts."""
        alerts = []

        # Quality score alerts
        if avg_quality_score < 0.7:
            alerts.append(
                {
                    "type": "LOW_QUALITY_SCORE",
                    "severity": "WARNING" if avg_quality_score >= 0.5 else "CRITICAL",
                    "message": f"Average quality score is low: {avg_quality_score:.2f}",
                    "threshold": 0.7,
                    "current_value": avg_quality_score,
                }
            )

        # Citation count alerts
        if avg_citation_count < 5:
            alerts.append(
                {
                    "type": "LOW_CITATION_COUNT",
                    "severity": "WARNING",
                    "message": f"Average citation count is low: {avg_citation_count}",
                    "threshold": 5,
                    "current_value": avg_citation_count,
                }
            )

        # Failure rate alerts
        if total_generations > 0:
            failure_rate = failed_generations / total_generations
            if failure_rate > 0.2:  # 20% failure rate
                alerts.append(
                    {
                        "type": "HIGH_FAILURE_RATE",
                        "severity": "CRITICAL" if failure_rate > 0.5 else "WARNING",
                        "message": f"High generation failure rate: {failure_rate:.1%}",
                        "threshold": 0.2,
                        "current_value": failure_rate,
                    }
                )

        return alerts


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _metrics_collector


@contextmanager
def measure_time(operation_name: str):
    """Context manager to measure operation time."""
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Operation completed: {operation_name}",
            extra={"operation": operation_name, "duration_ms": duration_ms},
        )


class PerformanceMonitor:
    """Performance monitoring utilities."""

    @staticmethod
    def monitor_function(func_name: str = None):
        """Decorator to monitor function performance."""

        def decorator(func):
            name = func_name or f"{func.__module__}.{func.__name__}"

            def wrapper(*args, **kwargs):
                with measure_time(name):
                    return func(*args, **kwargs)

            async def async_wrapper(*args, **kwargs):
                with measure_time(name):
                    return await func(*args, **kwargs)

            return (
                async_wrapper
                if hasattr(func, "__code__") and func.__code__.co_flags & 0x80
                else wrapper
            )

        return decorator

    @staticmethod
    def check_memory_usage(threshold_mb: float = 500.0):
        """Check if memory usage exceeds threshold."""
        memory = psutil.virtual_memory()
        used_mb = memory.used / (1024 * 1024)

        if used_mb > threshold_mb:
            logger.warning(
                f"High memory usage detected: {used_mb:.1f}MB",
                extra={
                    "memory_used_mb": used_mb,
                    "memory_threshold_mb": threshold_mb,
                    "memory_percent": memory.percent,
                },
            )
            return True
        return False

    @staticmethod
    def check_disk_usage(threshold_percent: float = 80.0):
        """Check if disk usage exceeds threshold."""
        disk = psutil.disk_usage("/")

        if disk.percent > threshold_percent:
            logger.warning(
                f"High disk usage detected: {disk.percent:.1f}%",
                extra={
                    "disk_percent": disk.percent,
                    "disk_threshold_percent": threshold_percent,
                    "disk_free_gb": disk.free / (1024 * 1024 * 1024),
                },
            )
            return True
        return False


# Health check utilities
class HealthChecker:
    """System health checking utilities."""

    @staticmethod
    async def check_database_health() -> dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            from crypto_newsletter.shared.database.connection import get_db_session

            start_time = time.time()
            async with get_db_session() as db:
                await db.execute("SELECT 1")
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "message": "Database connection successful",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"Database connection failed: {str(e)}",
            }

    @staticmethod
    def check_redis_health() -> dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            import redis

            start_time = time.time()
            r = redis.from_url(get_settings().redis_url)
            r.ping()
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "message": "Redis connection successful",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"Redis connection failed: {str(e)}",
            }

    @staticmethod
    async def check_external_api_health() -> dict[str, Any]:
        """Check external API connectivity."""
        try:
            from crypto_newsletter.core.ingestion.coindesk_client import (
                CoinDeskAPIClient,
            )

            start_time = time.time()
            client = CoinDeskAPIClient()
            # Test with minimal request
            await client.fetch_articles(limit=1)
            response_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "message": "External API accessible",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"External API failed: {str(e)}",
            }
