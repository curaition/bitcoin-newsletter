"""Redis connection health monitoring for Celery services."""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

import redis
from celery import Celery
from kombu.exceptions import OperationalError

from crypto_newsletter.shared.config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisHealthMonitor:
    """Monitor Redis connection health for Celery services."""
    
    def __init__(self, celery_app: Optional[Celery] = None):
        """Initialize Redis health monitor."""
        self.settings = get_settings()
        self.celery_app = celery_app
        self._redis_client: Optional[redis.Redis] = None
        
    @property
    def redis_client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._redis_client is None:
            # Parse Redis URL to create direct connection
            redis_url = self.settings.effective_celery_broker_url
            self._redis_client = redis.from_url(
                redis_url,
                socket_timeout=10,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
        return self._redis_client
    
    def check_redis_connection(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        start_time = time.time()
        result = {
            "status": "unknown",
            "response_time_ms": 0,
            "error": None,
            "details": {}
        }
        
        try:
            # Test basic connectivity
            pong = self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            if pong:
                result.update({
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "details": {
                        "ping_successful": True,
                        "connection_pool_size": len(self.redis_client.connection_pool._available_connections),
                        "connection_pool_max": self.redis_client.connection_pool.max_connections,
                    }
                })
                
                # Get additional Redis info
                try:
                    info = self.redis_client.info()
                    result["details"].update({
                        "redis_version": info.get("redis_version"),
                        "connected_clients": info.get("connected_clients"),
                        "used_memory_human": info.get("used_memory_human"),
                        "uptime_in_seconds": info.get("uptime_in_seconds"),
                    })
                except Exception as e:
                    logger.warning(f"Could not get Redis info: {e}")
                    
            else:
                result.update({
                    "status": "unhealthy",
                    "response_time_ms": round(response_time, 2),
                    "error": "Redis ping returned False"
                })
                
        except redis.ConnectionError as e:
            response_time = (time.time() - start_time) * 1000
            result.update({
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": f"Redis connection error: {str(e)}"
            })
            logger.error(f"Redis connection failed: {e}")
            
        except redis.TimeoutError as e:
            response_time = (time.time() - start_time) * 1000
            result.update({
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": f"Redis timeout error: {str(e)}"
            })
            logger.error(f"Redis timeout: {e}")
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result.update({
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": f"Unexpected error: {str(e)}"
            })
            logger.error(f"Unexpected Redis error: {e}")
            
        return result
    
    def check_celery_broker_connection(self) -> Dict[str, Any]:
        """Check Celery broker connection health."""
        if not self.celery_app:
            return {
                "status": "unknown",
                "error": "No Celery app provided"
            }
            
        start_time = time.time()
        result = {
            "status": "unknown",
            "response_time_ms": 0,
            "error": None,
            "details": {}
        }
        
        try:
            # Test broker connection
            with self.celery_app.connection() as conn:
                conn.ensure_connection(max_retries=3)
                response_time = (time.time() - start_time) * 1000
                
                result.update({
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "details": {
                        "broker_url": self.celery_app.conf.broker_url,
                        "transport": conn.transport_cls.__name__,
                        "connection_established": True,
                    }
                })
                
        except OperationalError as e:
            response_time = (time.time() - start_time) * 1000
            result.update({
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": f"Celery broker connection error: {str(e)}"
            })
            logger.error(f"Celery broker connection failed: {e}")
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result.update({
                "status": "unhealthy",
                "response_time_ms": round(response_time, 2),
                "error": f"Unexpected Celery error: {str(e)}"
            })
            logger.error(f"Unexpected Celery error: {e}")
            
        return result
    
    def get_comprehensive_health_check(self) -> Dict[str, Any]:
        """Get comprehensive health check for Redis and Celery."""
        redis_health = self.check_redis_connection()
        celery_health = self.check_celery_broker_connection()
        
        # Determine overall status
        overall_status = "healthy"
        if redis_health["status"] != "healthy" or celery_health["status"] != "healthy":
            overall_status = "unhealthy"
        elif redis_health["status"] == "unknown" or celery_health["status"] == "unknown":
            overall_status = "unknown"
            
        return {
            "overall_status": overall_status,
            "timestamp": time.time(),
            "checks": {
                "redis": redis_health,
                "celery_broker": celery_health,
            }
        }
    
    @contextmanager
    def safe_redis_operation(self, operation_name: str = "redis_operation"):
        """Context manager for safe Redis operations with error handling."""
        try:
            # Check connection before operation
            health = self.check_redis_connection()
            if health["status"] != "healthy":
                raise redis.ConnectionError(f"Redis unhealthy: {health.get('error', 'Unknown error')}")
                
            yield self.redis_client
            
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error during {operation_name}: {e}")
            raise
        except redis.TimeoutError as e:
            logger.error(f"Redis timeout during {operation_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during {operation_name}: {e}")
            raise
    
    def close(self):
        """Close Redis connection."""
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis_client = None


def get_redis_health_monitor(celery_app: Optional[Celery] = None) -> RedisHealthMonitor:
    """Get Redis health monitor instance."""
    return RedisHealthMonitor(celery_app)


def check_redis_health() -> Dict[str, Any]:
    """Quick Redis health check function."""
    monitor = get_redis_health_monitor()
    try:
        return monitor.check_redis_connection()
    finally:
        monitor.close()


def check_celery_health(celery_app: Celery) -> Dict[str, Any]:
    """Quick Celery health check function."""
    monitor = get_redis_health_monitor(celery_app)
    try:
        return monitor.get_comprehensive_health_check()
    finally:
        monitor.close()
