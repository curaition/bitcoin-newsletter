#!/usr/bin/env python3
"""
Deployment script to apply worker connectivity fixes to production.
This script helps deploy the heartbeat fix and validate the deployment.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def check_deployment_status():
    """Check the status of the deployment and worker connectivity."""
    print("🚀 Checking Deployment Status...")
    print("=" * 50)

    # Import after path setup
    try:
        from crypto_newsletter.shared.celery.worker import get_worker_health
        from crypto_newsletter.shared.config.settings import get_settings

        settings = get_settings()
        print(f"Environment: {settings.environment}")
        print(f"Service Type: {settings.service_type}")
        print()

        # Wait a moment for workers to register after deployment
        print("⏳ Waiting 30 seconds for workers to register...")
        await asyncio.sleep(30)

        # Check worker health
        print("🏥 Checking Worker Health...")
        worker_health = await get_worker_health()
        print(f"Worker Health: {worker_health}")

        if worker_health.get("status") == "healthy":
            print("✅ SUCCESS: Workers are now detected and healthy!")
            print(f"Workers found: {worker_health.get('workers', 0)}")
            return True
        else:
            print(f"❌ Workers still not detected: {worker_health.get('message')}")
            return False

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def validate_api_status():
    """Validate that the API status endpoint now shows healthy workers."""
    print("\n🌐 Validating API Status Endpoint...")

    try:
        import httpx

        # Check the production API status
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://bitcoin-newsletter-api.onrender.com/admin/status", timeout=30.0
            )

            if response.status_code == 200:
                status_data = response.json()
                celery_status = status_data.get("celery", {})

                print(f"API Status: {response.status_code}")
                print(f"Celery Status: {celery_status.get('status')}")

                workers_info = celery_status.get("workers", {})
                if isinstance(workers_info, dict):
                    worker_count = workers_info.get("workers", 0)
                    print(f"Workers Detected: {worker_count}")

                    if worker_count > 0:
                        print("✅ SUCCESS: API now reports healthy workers!")
                        return True
                    else:
                        print("❌ API still reports no workers")
                        return False
                else:
                    print(f"❌ Unexpected workers info format: {workers_info}")
                    return False
            else:
                print(f"❌ API request failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ API validation failed: {e}")
        return False


def print_deployment_instructions():
    """Print instructions for deploying the fix."""
    print("📋 DEPLOYMENT INSTRUCTIONS")
    print("=" * 50)
    print()
    print("The worker connectivity fix has been applied to the codebase.")
    print("To deploy this fix to production:")
    print()
    print("1. Commit the changes:")
    print("   git add .")
    print("   git commit -m 'Fix: Enable Celery worker heartbeat for health detection'")
    print()
    print("2. Push to trigger Render deployment:")
    print("   git push origin main")
    print()
    print("3. Monitor Render deployment:")
    print("   - Worker service will restart automatically")
    print("   - Wait ~2-3 minutes for deployment to complete")
    print()
    print("4. Validate the fix:")
    print("   - Check https://bitcoin-newsletter-api.onrender.com/admin/status")
    print("   - Workers should now show as 'healthy' with count > 0")
    print()
    print("🔧 CHANGES MADE:")
    print("- Removed --without-heartbeat from worker startup")
    print("- Reduced broker_heartbeat to 30 seconds for better detection")
    print("- Added worker health monitoring improvements")
    print()


async def main():
    """Main deployment validation function."""
    print("🔧 CELERY WORKER CONNECTIVITY FIX")
    print("=" * 50)
    print()

    # Check if we're in production environment
    try:
        from crypto_newsletter.shared.config.settings import get_settings

        settings = get_settings()

        if settings.environment == "production":
            print("🏭 Running in PRODUCTION environment")
            print("Validating deployment...")

            # Check deployment status
            worker_success = await check_deployment_status()
            api_success = await validate_api_status()

            if worker_success and api_success:
                print("\n🎉 DEPLOYMENT SUCCESSFUL!")
                print("Worker connectivity issue has been resolved.")
            else:
                print("\n⚠️ DEPLOYMENT NEEDS ATTENTION")
                print("Some checks failed. Review the output above.")

        else:
            print(f"🧪 Running in {settings.environment.upper()} environment")
            print_deployment_instructions()

    except Exception as e:
        print(f"❌ Error during validation: {e}")
        print_deployment_instructions()


if __name__ == "__main__":
    asyncio.run(main())
