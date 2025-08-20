"""Celery worker entry point and configuration."""

import signal
import sys
from typing import Any

from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_retry,
    task_success,
    worker_ready,
    worker_shutdown,
)
from crypto_newsletter.shared.celery.app import (
    configure_celery_for_environment,
)
from loguru import logger

# Configure Celery for current environment
app = configure_celery_for_environment()


# Signal handlers for task lifecycle monitoring
@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
):
    """Handle task pre-run events."""
    logger.info(f"Task starting: {task.name} [{task_id}]")


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **kwds,
):
    """Handle task post-run events."""
    logger.info(f"Task completed: {task.name} [{task_id}] - State: {state}")


@task_success.connect
def task_success_handler(sender=None, result=None, **kwds):
    """Handle successful task completion."""
    logger.debug(f"Task succeeded: {sender.name}")


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds
):
    """Handle task failures."""
    logger.error(f"Task failed: {sender.name} [{task_id}] - {exception}")


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handle task retries."""
    logger.warning(f"Task retrying: {sender.name} [{task_id}] - Reason: {reason}")


@worker_ready.connect
def worker_ready_handler(sender=None, **kwds):
    """Handle worker ready events."""
    logger.info(f"Celery worker ready: {sender.hostname}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwds):
    """Handle worker shutdown events."""
    logger.info(f"Celery worker shutting down: {sender.hostname}")


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        app.control.broadcast("shutdown")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def start_worker(
    loglevel: str = "INFO",
    concurrency: int = 10,  # Moderate concurrency for AsyncIO pool
    queues: str = "default,ingestion,monitoring,maintenance,batch_processing,newsletter,publishing",
    **kwargs,
) -> None:
    """
    Start Celery worker with specified configuration.

    Args:
        loglevel: Logging level for the worker
        concurrency: Number of concurrent worker processes
        queues: Comma-separated list of queues to consume from
        **kwargs: Additional worker options
    """
    setup_signal_handlers()

    logger.info(
        f"Starting Celery worker - concurrency: {concurrency}, queues: {queues}"
    )

    # Configure AsyncIO pool as custom worker pool
    import os

    os.environ["CELERY_CUSTOM_WORKER_POOL"] = "celery_aio_pool.pool:AsyncIOPool"

    # Start the worker with AsyncIO pool
    app.worker_main(
        [
            "worker",
            f"--loglevel={loglevel}",
            f"--concurrency={concurrency}",
            f"--queues={queues}",
            "--pool=custom",  # Use custom AsyncIO pool
            "--without-gossip",
            "--without-mingle",
            # Removed --without-heartbeat to enable worker detection
        ]
        + [f"--{k}={v}" for k, v in kwargs.items()]
    )


def start_beat(loglevel: str = "INFO", **kwargs) -> None:
    """
    Start Celery beat scheduler.

    Args:
        loglevel: Logging level for the beat scheduler
        **kwargs: Additional beat options
    """
    import os
    import sys

    setup_signal_handlers()

    logger.info("Starting Celery beat scheduler")

    # Ensure Django is set up for beat scheduler
    try:
        from crypto_newsletter.shared.django_minimal import setup_django

        setup_django()
        logger.info("Django setup completed for beat scheduler")
    except Exception as e:
        logger.warning(f"Could not setup Django for beat scheduler: {e}")

    # Set SERVICE_TYPE environment variable for beat
    os.environ["SERVICE_TYPE"] = "beat"

    # Start the beat scheduler using subprocess to avoid argv issues
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "crypto_newsletter.shared.celery.app:celery_app",
        "beat",
        f"--loglevel={loglevel}",
        "--pidfile=",  # Disable pidfile for Railway
    ]

    # Add additional kwargs as command line arguments
    for k, v in kwargs.items():
        cmd.extend([f"--{k}", str(v)])

    logger.info(f"Executing: {' '.join(cmd)}")
    os.execvp(sys.executable, cmd)


def start_flower(port: int = 5555, **kwargs) -> None:
    """
    Start Flower monitoring interface.

    Args:
        port: Port to run Flower on
        **kwargs: Additional Flower options
    """
    logger.info(f"Starting Flower monitoring on port {port}")

    # Start Flower
    app.worker_main(
        [
            "flower",
            f"--port={port}",
            "--basic_auth=admin:admin",  # Basic auth for Railway
        ]
        + [f"--{k}={v}" for k, v in kwargs.items()]
    )


# Health check utilities for monitoring
async def get_worker_health() -> dict[str, Any]:
    """Get health status of Celery workers."""
    try:
        inspect = app.control.inspect()

        # Get worker stats
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()

        if not stats:
            return {
                "status": "unhealthy",
                "message": "No workers available",
                "workers": 0,
            }

        worker_count = len(stats)
        total_active_tasks = sum(len(tasks) for tasks in (active or {}).values())
        total_scheduled_tasks = sum(len(tasks) for tasks in (scheduled or {}).values())

        return {
            "status": "healthy",
            "message": f"{worker_count} workers active",
            "workers": worker_count,
            "active_tasks": total_active_tasks,
            "scheduled_tasks": total_scheduled_tasks,
            "worker_details": stats,
        }

    except Exception as exc:
        logger.error(f"Worker health check failed: {exc}")
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {exc}",
            "workers": 0,
        }


async def get_queue_health() -> dict[str, Any]:
    """Get health status of Celery queues."""
    try:
        inspect = app.control.inspect()

        # Get queue lengths (if broker supports it)
        try:
            queue_lengths = inspect.active_queues()
            return {
                "status": "healthy",
                "message": "Queues accessible",
                "queues": queue_lengths,
            }
        except Exception:
            # Fallback if queue inspection not supported
            return {
                "status": "healthy",
                "message": "Queue inspection not supported by broker",
                "queues": {},
            }

    except Exception as exc:
        logger.error(f"Queue health check failed: {exc}")
        return {
            "status": "unhealthy",
            "message": f"Queue check failed: {exc}",
            "queues": {},
        }


if __name__ == "__main__":
    # Default worker startup
    start_worker()
