#!/usr/bin/env python3
"""
Local testing script for worker connectivity fix.
This script helps test the worker heartbeat changes locally before deployment.
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_prerequisites():
    """Check if local environment is ready for testing."""
    print("🔍 Checking Local Prerequisites...")
    print("=" * 50)

    # Check if Redis is running
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        print("✅ Redis is running on localhost:6379")
    except Exception as e:
        print(f"❌ Redis not available: {e}")
        print(
            "   Start Redis with: brew services start redis (macOS) or sudo systemctl start redis (Linux)"
        )
        return False

    # Check if required packages are installed
    try:
        import celery

        print(f"✅ Celery installed: {celery.__version__}")
    except ImportError:
        print("❌ Celery not installed")
        print("   Install with: uv add celery[redis]")
        return False

    try:
        import celery_aio_pool

        print("✅ celery-aio-pool available")
    except ImportError:
        print("❌ celery-aio-pool not installed")
        print("   Install with: uv add celery-aio-pool")
        return False

    # Check environment variables
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  No .env file found - using defaults")

    return True


def setup_test_environment():
    """Set up environment variables for local testing."""
    print("\n🔧 Setting Up Test Environment...")

    # Set minimal required environment variables
    os.environ.update(
        {
            "ENVIRONMENT": "development",
            "SERVICE_TYPE": "worker",
            "REDIS_URL": "redis://localhost:6379/0",
            "ENABLE_CELERY": "true",
            "DATABASE_URL": "postgresql://localhost:5432/test_db",  # Won't be used for worker test
            "COINDESK_API_KEY": "test_key",  # Won't be used for worker test
            "LOG_LEVEL": "INFO",
            "DEBUG": "true",
        }
    )

    print("✅ Environment variables set for testing")


async def test_worker_health_before_fix():
    """Test worker health detection with the current (fixed) configuration."""
    print("\n🏥 Testing Worker Health Detection...")
    print("=" * 50)

    try:
        from crypto_newsletter.shared.celery.app import celery_app
        from crypto_newsletter.shared.celery.worker import (
            get_queue_health,
            get_worker_health,
        )

        # Test broker connection first
        print("🔗 Testing broker connection...")
        try:
            with celery_app.connection() as conn:
                conn.ensure_connection(max_retries=3)
                print("✅ Broker connection successful")
        except Exception as e:
            print(f"❌ Broker connection failed: {e}")
            return False

        # Test worker health (should show no workers initially)
        print("\n👥 Testing worker health detection...")
        worker_health = await get_worker_health()
        print(f"Worker Health: {worker_health}")

        # Test queue health
        print("\n📋 Testing queue health...")
        queue_health = await get_queue_health()
        print(f"Queue Health: {queue_health}")

        return True

    except Exception as e:
        print(f"❌ Health test failed: {e}")
        return False


def start_test_worker():
    """Start a test worker in the background."""
    print("\n🚀 Starting Test Worker...")
    print("=" * 50)

    try:
        # Start worker in background
        cmd = [
            sys.executable,
            "-m",
            "crypto_newsletter.cli.main",
            "worker",
            "--loglevel",
            "INFO",
            "--concurrency",
            "2",
        ]

        print(f"Starting worker with command: {' '.join(cmd)}")

        # Start worker process
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        print(f"✅ Worker started with PID: {process.pid}")
        print("⏳ Waiting 10 seconds for worker to register...")
        time.sleep(10)

        return process

    except Exception as e:
        print(f"❌ Failed to start worker: {e}")
        return None


async def test_worker_detection_after_start():
    """Test if workers are detected after starting."""
    print("\n🔍 Testing Worker Detection After Start...")
    print("=" * 50)

    try:
        from crypto_newsletter.shared.celery.worker import get_worker_health

        # Test worker detection
        worker_health = await get_worker_health()
        print(f"Worker Health After Start: {worker_health}")

        if worker_health.get("status") == "healthy":
            worker_count = worker_health.get("workers", 0)
            print(f"✅ SUCCESS: {worker_count} worker(s) detected!")
            return True
        else:
            print(f"❌ Workers still not detected: {worker_health.get('message')}")
            return False

    except Exception as e:
        print(f"❌ Worker detection test failed: {e}")
        return False


def cleanup_test_worker(process):
    """Clean up the test worker process."""
    if process:
        print("\n🧹 Cleaning up test worker...")
        try:
            process.terminate()
            process.wait(timeout=10)
            print("✅ Worker process terminated cleanly")
        except subprocess.TimeoutExpired:
            process.kill()
            print("⚠️  Worker process killed (timeout)")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")


async def main():
    """Main testing function."""
    print("🧪 LOCAL WORKER CONNECTIVITY TEST")
    print("=" * 50)
    print("This script tests the worker heartbeat fix locally")
    print("before deploying to production.\n")

    # Step 1: Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return

    # Step 2: Setup environment
    setup_test_environment()

    # Step 3: Test health detection (no workers running)
    health_test_passed = await test_worker_health_before_fix()
    if not health_test_passed:
        print("\n❌ Basic health test failed. Check your setup.")
        return

    # Step 4: Start test worker
    worker_process = start_test_worker()
    if not worker_process:
        print("\n❌ Failed to start test worker.")
        return

    try:
        # Step 5: Test worker detection
        detection_passed = await test_worker_detection_after_start()

        if detection_passed:
            print("\n🎉 LOCAL TEST SUCCESSFUL!")
            print("The worker heartbeat fix is working correctly.")
            print("Workers are now properly detected by the health system.")
            print("\n✅ Ready for production deployment!")
        else:
            print("\n❌ LOCAL TEST FAILED!")
            print("Workers are still not being detected.")
            print("The fix may need additional adjustments.")

    finally:
        # Step 6: Cleanup
        cleanup_test_worker(worker_process)

    print("\n📋 Next Steps:")
    if detection_passed:
        print("1. The fix is validated locally")
        print("2. You can now safely deploy to production")
        print("3. Run: git add . && git commit -m 'Fix: Enable worker heartbeat'")
        print("4. Run: git push origin main")
    else:
        print("1. Review the worker startup configuration")
        print("2. Check Redis connection and Celery setup")
        print("3. Debug the heartbeat detection issue")


if __name__ == "__main__":
    asyncio.run(main())
