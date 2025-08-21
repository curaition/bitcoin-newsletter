#!/usr/bin/env python3
"""
Diagnostic script to identify the root cause of worker connectivity issues.
This will help us understand what's different between local and production.
"""

import asyncio

import httpx


async def diagnose_production_environment():
    """Diagnose the production environment to find the root cause."""
    print("🔍 PRODUCTION ENVIRONMENT DIAGNOSIS")
    print("=" * 60)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Get detailed status information
            print("1. 📊 Checking detailed system status...")
            status_response = await client.get(
                "https://bitcoin-newsletter-api.onrender.com/admin/status"
            )

            if status_response.status_code == 200:
                status_data = status_response.json()

                # Print environment info
                print(f"   Environment: {status_data.get('environment')}")
                print(f"   Service: {status_data.get('service')}")
                print(f"   Timestamp: {status_data.get('timestamp')}")

                # Check API status
                api_info = status_data.get("api", {})
                print(f"\n   API Status: {api_info.get('status')}")
                print(f"   API Environment: {api_info.get('environment')}")

                # Check database connectivity
                db_info = status_data.get("database", {})
                print(f"\n   Database Status: {db_info.get('status')}")
                print(f"   Total Articles: {db_info.get('total_articles')}")

                # Detailed Celery analysis
                celery_info = status_data.get("celery", {})
                print("\n2. 🔧 Celery Configuration Analysis:")
                print(f"   Enabled: {celery_info.get('enabled')}")
                print(f"   Status: {celery_info.get('status')}")

                # Worker details
                workers_info = celery_info.get("workers", {})
                print(f"\n   Workers Status: {workers_info.get('status')}")
                print(f"   Workers Count: {workers_info.get('workers')}")
                print(f"   Workers Message: {workers_info.get('message')}")

                # Check for any error information
                if "error" in celery_info:
                    print(f"   ❌ Celery Error: {celery_info['error']}")

                # Active tasks info
                tasks_info = celery_info.get("active_tasks", {})
                print(f"\n   Active Tasks: {tasks_info.get('active', 0)}")
                print(f"   Scheduled Tasks: {tasks_info.get('scheduled', 0)}")
                print(f"   Reserved Tasks: {tasks_info.get('reserved', 0)}")

                return status_data
            else:
                print(f"   ❌ Status endpoint failed: {status_response.status_code}")
                return None

    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        return None


async def compare_with_local_config():
    """Compare production config with local working config."""
    print("\n3. 🔄 Comparing with Local Configuration:")
    print("   Local Redis URL: redis://localhost:6379/0")
    print("   Production Redis: fromService (Render Redis)")
    print("   Local Worker Command: python -m crypto_newsletter.cli.main worker")
    print("   Production Worker Command: crypto-newsletter worker")
    print("   Local Environment: development")
    print("   Production Environment: production")


async def suggest_debugging_steps():
    """Suggest next debugging steps based on findings."""
    print("\n4. 🔧 Debugging Steps to Try:")
    print("   A. Check if Redis service is accessible from worker")
    print("   B. Verify worker service logs in Render dashboard")
    print("   C. Test if worker can connect to broker at startup")
    print("   D. Check if there are any network connectivity issues")
    print("   E. Verify environment variables are properly set")

    print("\n5. 🎯 Potential Root Causes:")
    print("   1. Redis service connectivity issues")
    print("   2. Worker service startup failures")
    print("   3. Environment variable configuration problems")
    print("   4. Network policies blocking worker-to-redis communication")
    print("   5. Service startup timing issues")


async def test_specific_endpoints():
    """Test specific endpoints that might give us more info."""
    print("\n6. 🧪 Testing Additional Endpoints:")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test if there are any other health endpoints
            endpoints_to_test = [
                "/health",
                "/admin/status",
                # Add any other diagnostic endpoints if they exist
            ]

            for endpoint in endpoints_to_test:
                try:
                    response = await client.get(
                        f"https://bitcoin-newsletter-api.onrender.com{endpoint}"
                    )
                    print(f"   {endpoint}: {response.status_code}")
                    if response.status_code != 200:
                        print(f"      Error: {response.text[:100]}...")
                except Exception as e:
                    print(f"   {endpoint}: Failed - {e}")

    except Exception as e:
        print(f"   ❌ Endpoint testing failed: {e}")


async def main():
    """Main diagnostic function."""
    print("🚨 INVESTIGATING WORKER CONNECTIVITY ROOT CAUSE")
    print("=" * 60)
    print("API keys are confirmed to be properly configured.")
    print("Local testing shows heartbeat fix works correctly.")
    print("Production workers still not detected - investigating why...")
    print()

    # Run comprehensive diagnosis
    status_data = await diagnose_production_environment()
    await compare_with_local_config()
    await test_specific_endpoints()
    await suggest_debugging_steps()

    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")

    if status_data:
        celery_info = status_data.get("celery", {})
        if (
            celery_info.get("enabled")
            and celery_info.get("workers", {}).get("workers") == 0
        ):
            print("✅ Celery is enabled and configured")
            print("❌ Workers are not connecting to broker")
            print("🔍 Root cause is likely:")
            print("   - Redis connectivity between worker and Redis service")
            print("   - Worker service startup failure")
            print("   - Network/firewall issues in Render environment")
            print("\n💡 NEXT STEP: Check Render worker service logs for startup errors")
        else:
            print("❌ Celery configuration issue detected")
    else:
        print("❌ Could not retrieve diagnostic information")


if __name__ == "__main__":
    asyncio.run(main())
