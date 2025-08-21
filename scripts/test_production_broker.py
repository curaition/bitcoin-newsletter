#!/usr/bin/env python3
"""
Test script to check broker connectivity from production API.
This will help us understand if the issue is with Redis connection or worker startup.
"""

import asyncio

import httpx


async def test_broker_connectivity():
    """Test if we can connect to the broker from the API service."""
    print("🔍 Testing Production Broker Connectivity...")
    print("=" * 50)

    try:
        # Test the health endpoint first
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("1. Testing API health...")
            health_response = await client.get(
                "https://bitcoin-newsletter-api.onrender.com/health"
            )
            print(f"   API Health: {health_response.status_code}")

            print("\n2. Testing admin status...")
            status_response = await client.get(
                "https://bitcoin-newsletter-api.onrender.com/admin/status"
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                celery_info = status_data.get("celery", {})

                print(f"   Celery Enabled: {celery_info.get('enabled')}")
                print(f"   Celery Status: {celery_info.get('status')}")

                workers_info = celery_info.get("workers", {})
                print(f"   Workers Status: {workers_info.get('status')}")
                print(f"   Workers Count: {workers_info.get('workers')}")
                print(f"   Workers Message: {workers_info.get('message')}")

                # Check if there are any error details
                if "error" in celery_info:
                    print(f"   Celery Error: {celery_info['error']}")

                return celery_info
            else:
                print(f"   Status endpoint failed: {status_response.status_code}")
                return None

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


async def main():
    """Main test function."""
    print("🧪 PRODUCTION BROKER CONNECTIVITY TEST")
    print("=" * 50)

    result = await test_broker_connectivity()

    if result:
        workers_info = result.get("workers", {})
        if workers_info.get("status") == "healthy":
            print("\n✅ SUCCESS: Workers are detected and healthy!")
            print("The heartbeat fix is working correctly.")
        else:
            print("\n❌ ISSUE: Workers still not detected")
            print("Possible causes:")
            print("1. Worker service failed to start")
            print("2. Redis connection issues")
            print("3. Worker crashed due to missing dependencies")
            print("4. Heartbeat configuration still not working")

            print("\n🔧 Next steps:")
            print("1. Check Render worker service logs")
            print("2. Verify Redis service connectivity")
            print("3. Check if API keys are configured")
    else:
        print("\n❌ Could not retrieve status information")


if __name__ == "__main__":
    asyncio.run(main())
