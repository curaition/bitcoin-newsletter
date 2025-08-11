"""Metrics collection and monitoring utilities."""

import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from loguru import logger
from crypto_newsletter.shared.config.settings import get_settings


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
    load_average: List[float]
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
    queue_lengths: Dict[str, int]


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
            disk = psutil.disk_usage('/')
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
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk.percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                load_average=load_avg,
                process_count=process_count
            )
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                load_average=[0.0, 0.0, 0.0],
                process_count=0
            )
    
    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics."""
        uptime = time.time() - self.start_time
        avg_response_time = (
            sum(self._response_times) / len(self._response_times)
            if self._response_times else 0.0
        )
        
        cache_total = self._cache_hits + self._cache_misses
        cache_hit_rate = (
            self._cache_hits / cache_total if cache_total > 0 else 0.0
        )
        
        return ApplicationMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            service_type=self.settings.service_type,
            uptime_seconds=uptime,
            active_connections=self._get_active_connections(),
            total_requests=self._request_count,
            error_count=self._error_count,
            avg_response_time_ms=avg_response_time,
            cache_hit_rate=cache_hit_rate
        )
    
    async def collect_database_metrics(self) -> DatabaseMetrics:
        """Collect database performance metrics."""
        try:
            from crypto_newsletter.shared.database.connection import get_db_session
            from crypto_newsletter.core.storage.repository import ArticleRepository
            
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
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    connection_count=connection_count,
                    active_queries=active_queries,
                    total_articles=stats.get("total_articles", 0),
                    articles_today=stats.get("recent_articles_24h", 0),
                    avg_query_time_ms=0.0,  # Would need query performance tracking
                    slow_queries_count=0    # Would need slow query log analysis
                )
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return DatabaseMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                connection_count=0,
                active_queries=0,
                total_articles=0,
                articles_today=0,
                avg_query_time_ms=0.0,
                slow_queries_count=0
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
                timestamp=datetime.now(timezone.utc).isoformat(),
                active_tasks=active_count,
                pending_tasks=sum(queue_lengths.values()),
                completed_tasks_today=0,  # Would need task result tracking
                failed_tasks_today=0,     # Would need task result tracking
                avg_task_duration_ms=0.0, # Would need task timing tracking
                queue_lengths=queue_lengths
            )
        except Exception as e:
            logger.error(f"Failed to collect task metrics: {e}")
            return TaskMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                active_tasks=0,
                pending_tasks=0,
                completed_tasks_today=0,
                failed_tasks_today=0,
                avg_task_duration_ms=0.0,
                queue_lengths={}
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
        
        logger.debug("Request recorded", extra={
            "response_time_ms": response_time_ms,
            "status_code": status_code,
            "total_requests": self._request_count
        })
    
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
    
    def _get_queue_lengths(self) -> Dict[str, int]:
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
        logger.info(f"Operation completed: {operation_name}", extra={
            "operation": operation_name,
            "duration_ms": duration_ms
        })


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
            
            return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else wrapper
        return decorator
    
    @staticmethod
    def check_memory_usage(threshold_mb: float = 500.0):
        """Check if memory usage exceeds threshold."""
        memory = psutil.virtual_memory()
        used_mb = memory.used / (1024 * 1024)
        
        if used_mb > threshold_mb:
            logger.warning(f"High memory usage detected: {used_mb:.1f}MB", extra={
                "memory_used_mb": used_mb,
                "memory_threshold_mb": threshold_mb,
                "memory_percent": memory.percent
            })
            return True
        return False
    
    @staticmethod
    def check_disk_usage(threshold_percent: float = 80.0):
        """Check if disk usage exceeds threshold."""
        disk = psutil.disk_usage('/')
        
        if disk.percent > threshold_percent:
            logger.warning(f"High disk usage detected: {disk.percent:.1f}%", extra={
                "disk_percent": disk.percent,
                "disk_threshold_percent": threshold_percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            })
            return True
        return False


# Health check utilities
class HealthChecker:
    """System health checking utilities."""
    
    @staticmethod
    async def check_database_health() -> Dict[str, Any]:
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
                "message": "Database connection successful"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"Database connection failed: {str(e)}"
            }
    
    @staticmethod
    def check_redis_health() -> Dict[str, Any]:
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
                "message": "Redis connection successful"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"Redis connection failed: {str(e)}"
            }
    
    @staticmethod
    async def check_external_api_health() -> Dict[str, Any]:
        """Check external API connectivity."""
        try:
            from crypto_newsletter.core.ingestion.coindesk_client import CoinDeskAPIClient
            
            start_time = time.time()
            client = CoinDeskAPIClient()
            # Test with minimal request
            await client.fetch_articles(limit=1)
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "message": "External API accessible"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"External API failed: {str(e)}"
            }
