"""Celery application configuration and setup."""

# Essential imports for Railway compatibility

from celery import Celery
from celery.schedules import crontab
from crypto_newsletter.shared.config.settings import get_settings
from kombu import Queue


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    settings = get_settings()

    # Setup Django for beat scheduler (only when needed)
    if settings.service_type == "beat":
        try:
            from crypto_newsletter.shared.django_minimal import setup_django

            setup_django()
        except Exception as e:
            # Log warning but don't fail - beat service will handle this
            print(f"Warning: Could not setup Django for beat scheduler: {e}")

    # Create Celery app
    celery_app = Celery("crypto_newsletter")

    # Configure broker and backend
    celery_app.conf.update(
        broker_url=settings.effective_celery_broker_url,
        result_backend=settings.effective_celery_result_backend,
        # Task serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # Task routing and queues
        task_routes={
            "crypto_newsletter.core.scheduling.tasks.ingest_articles": {
                "queue": "ingestion"
            },
            "crypto_newsletter.core.scheduling.tasks.health_check": {
                "queue": "monitoring"
            },
            "crypto_newsletter.core.scheduling.tasks.cleanup_old_articles": {
                "queue": "maintenance"
            },
            "crypto_newsletter.newsletter.tasks.*": {"queue": "newsletter"},
            "crypto_newsletter.newsletter.batch.*": {"queue": "batch_processing"},
            "crypto_newsletter.newsletter.publishing.*": {"queue": "publishing"},
        },
        # Define queues
        task_default_queue="default",
        task_queues=(
            Queue("default", routing_key="default"),
            Queue("ingestion", routing_key="ingestion"),
            Queue("monitoring", routing_key="monitoring"),
            Queue("maintenance", routing_key="maintenance"),
            Queue("newsletter", routing_key="newsletter"),
            Queue("batch_processing", routing_key="batch_processing"),
            Queue("publishing", routing_key="publishing"),
        ),
        # Worker configuration - use solo pool to avoid mmap issues in containers
        worker_pool="solo",  # Changed from prefork to avoid mmap dependency
        worker_concurrency=1,  # Solo pool only supports concurrency=1
        worker_max_tasks_per_child=1000,
        worker_disable_rate_limits=False,
        # Task execution settings
        task_time_limit=1800,  # 30 minutes
        task_soft_time_limit=1500,  # 25 minutes
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_persistent=True,
        # Redis connection resilience settings
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=10,
        broker_connection_retry=True,
        broker_heartbeat=30,
        broker_pool_limit=10,
        # Redis-specific settings for connection stability
        redis_socket_timeout=30,  # 30 seconds (vs default 120)
        redis_socket_connect_timeout=10,  # 10 seconds connection timeout
        redis_retry_on_timeout=True,  # Retry on timeout
        redis_max_connections=20,  # Increase connection pool
        redis_socket_keepalive=True,  # Enable TCP keepalive
        redis_socket_keepalive_options={  # TCP keepalive options
            "TCP_KEEPIDLE": 1,
            "TCP_KEEPINTVL": 3,
            "TCP_KEEPCNT": 5,
        },
        # Beat schedule for periodic tasks
        beat_schedule={
            "ingest-articles-every-4-hours": {
                "task": "crypto_newsletter.core.scheduling.tasks.ingest_articles",
                "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
                "options": {
                    "priority": 9,
                    "retry_policy": {
                        "max_retries": 3,
                        "interval_start": 60,  # 1 minute
                        "interval_step": 60,  # 1 minute increments
                        "interval_max": 300,  # 5 minutes max
                    },
                },
            },
            "health-check-every-5-minutes": {
                "task": "crypto_newsletter.core.scheduling.tasks.health_check",
                "schedule": crontab(minute="*/5"),  # Every 5 minutes
                "options": {"priority": 8},
            },
            "cleanup-old-articles-daily": {
                "task": "crypto_newsletter.core.scheduling.tasks.cleanup_old_articles",
                "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM UTC
                "options": {"priority": 5},
            },
# Note: analyze-recent-articles task removed - batch processing is now handled
# by the dedicated batch processing system via manual/API triggers
        },
        # Beat scheduler configuration - only use database scheduler for beat service
        beat_scheduler="django_celery_beat.schedulers:DatabaseScheduler"
        if settings.service_type == "beat"
        else "celery.beat:PersistentScheduler",
        # Monitoring and logging
        worker_send_task_events=True,
        task_send_sent_event=True,
        # Error handling
        task_annotations={
            "*": {
                "rate_limit": "100/m",  # 100 tasks per minute max
                "time_limit": 1800,  # 30 minutes
                "soft_time_limit": 1500,  # 25 minutes
            }
        },
    )

    # Auto-discover tasks
    celery_app.autodiscover_tasks(
        [
            "crypto_newsletter.core.scheduling",
            "crypto_newsletter.analysis",
            "crypto_newsletter.newsletter.batch",
        ]
    )

    return celery_app


# Celery configuration for different environments
class CeleryConfig:
    """Celery configuration class."""

    @staticmethod
    def development_config(app: Celery) -> None:
        """Configure Celery for development environment."""
        app.conf.update(
            task_always_eager=False,  # Set to True to run tasks synchronously
            task_eager_propagates=True,
            worker_log_level="DEBUG",
            beat_schedule_filename="celerybeat-schedule-dev",
        )

    @staticmethod
    def production_config(app: Celery) -> None:
        """Configure Celery for production environment."""
        app.conf.update(
            task_always_eager=False,
            worker_log_level="WARNING",  # Reduced from INFO to prevent log spam
            worker_hijack_root_logger=False,
            beat_schedule_filename="celerybeat-schedule-prod",
            # Production optimizations
            worker_prefetch_multiplier=1,
            task_compression="gzip",
            result_compression="gzip",
            # Enhanced monitoring
            worker_send_task_events=True,
            task_send_sent_event=True,
            # Production error handling
            task_reject_on_worker_lost=True,
            task_acks_late=True,
            # Enhanced Redis connection resilience for production
            broker_connection_retry_on_startup=True,
            broker_connection_max_retries=15,  # More retries in production
            broker_heartbeat=60,  # Longer heartbeat for production
            redis_socket_timeout=45,  # Longer timeout for production
            redis_socket_connect_timeout=15,  # Longer connection timeout
        )

    @staticmethod
    def testing_config(app: Celery) -> None:
        """Configure Celery for testing environment."""
        app.conf.update(
            task_always_eager=True,  # Run tasks synchronously in tests
            task_eager_propagates=True,
            broker_url="memory://",
            result_backend="cache+memory://",
        )


def configure_celery_for_environment() -> Celery:
    """Configure Celery based on current environment."""
    settings = get_settings()
    app = create_celery_app()

    if settings.testing:
        CeleryConfig.testing_config(app)
    elif settings.is_production:
        CeleryConfig.production_config(app)
    else:
        CeleryConfig.development_config(app)

    return app


# Global Celery app instance - configured for environment
celery_app = configure_celery_for_environment()
