#!/usr/bin/env python3
"""
Test script to verify Celery worker connectivity and health reporting.
This script tests the worker health detection that was failing in production.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.celery.worker import get_queue_health, get_worker_health
from crypto_newsletter.shared.config.settings import get_settings


async def test_worker_connectivity():
    """Test worker connectivity and health reporting."""
    print("🔍 Testing Celery Worker Connectivity...")
    print("=" * 50)

    settings = get_settings()
    print(f"Environment: {settings.environment}")
    print(f"Celery Enabled: {settings.enable_celery}")
    print(f"Broker URL: {settings.effective_celery_broker_url}")
    print(f"Result Backend: {settings.effective_celery_result_backend}")
    print()

    # Test 1: Direct Celery inspection
    print("📊 Test 1: Direct Celery Inspection")
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        scheduled = inspect.scheduled()

        print(f"Stats: {stats}")
        print(f"Active tasks: {active}")
        print(f"Scheduled tasks: {scheduled}")

        if stats:
            print(f"✅ Found {len(stats)} workers via direct inspection")
        else:
            print("❌ No workers found via direct inspection")
    except Exception as e:
        print(f"❌ Direct inspection failed: {e}")

    print()

    # Test 2: Worker health function
    print("🏥 Test 2: Worker Health Function")
    try:
        worker_health = await get_worker_health()
        print(f"Worker Health Result: {worker_health}")

        if worker_health.get("status") == "healthy":
            print("✅ Worker health check passed")
        else:
            print(f"❌ Worker health check failed: {worker_health.get('message')}")
    except Exception as e:
        print(f"❌ Worker health check failed: {e}")

    print()

    # Test 3: Queue health function
    print("📋 Test 3: Queue Health Function")
    try:
        queue_health = await get_queue_health()
        print(f"Queue Health Result: {queue_health}")

        if queue_health.get("status") == "healthy":
            print("✅ Queue health check passed")
        else:
            print(f"❌ Queue health check failed: {queue_health.get('message')}")
    except Exception as e:
        print(f"❌ Queue health check failed: {e}")

    print()

    # Test 4: Broker connection test
    print("🔗 Test 4: Broker Connection Test")
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=3)
            print("✅ Broker connection successful")
    except Exception as e:
        print(f"❌ Broker connection failed: {e}")

    print()
    print("🎯 Test Summary:")
    print(
        "If workers are running but showing as unhealthy, the heartbeat fix should resolve this."
    )
    print("After deploying the fix, workers should be detected properly.")


if __name__ == "__main__":
    asyncio.run(test_worker_connectivity())
