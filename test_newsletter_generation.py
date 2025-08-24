#!/usr/bin/env python3
"""
Test script to trigger newsletter generation and validate the event loop fix.
"""

import json
import time

import requests


def test_newsletter_generation():
    """Test newsletter generation via API to validate event loop fix."""

    print("🧪 Testing Newsletter Generation - Event Loop Fix Validation")
    print("=" * 70)

    # API endpoint
    url = "https://bitcoin-newsletter-api.onrender.com/admin/newsletters/generate"

    # Request payload
    payload = {
        "newsletter_type": "DAILY",
        "force_generation": True,  # Force generation even if insufficient articles
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"📤 Sending POST request to: {url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")

        # Make the request
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"📥 Response Status: {response.status_code}")
        print(f"📄 Response Body: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")

            print("✅ Newsletter generation task started successfully!")
            print(f"🆔 Task ID: {task_id}")
            print(f"📊 Progress endpoint: {result.get('progress_endpoint', 'N/A')}")

            return task_id
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response JSON: {e}")
        return None


def monitor_task_progress(task_id, max_wait_minutes=10):
    """Monitor the task progress to see if it completes without event loop errors."""

    if not task_id:
        print("❌ No task ID provided for monitoring")
        return False

    print(f"\n🔍 Monitoring task progress: {task_id}")
    print("=" * 50)

    progress_url = (
        f"https://bitcoin-newsletter-api.onrender.com/admin/tasks/{task_id}/progress"
    )
    max_wait_seconds = max_wait_minutes * 60
    check_interval = 10  # Check every 10 seconds

    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(progress_url, timeout=10)

            if response.status_code == 200:
                progress = response.json()
                status = progress.get("status", "unknown")
                current_step = progress.get("current_step", "unknown")
                progress_pct = progress.get("progress_percentage", 0)

                print(
                    f"📊 Status: {status} | Step: {current_step} | Progress: {progress_pct}%"
                )

                if status in ["completed", "success"]:
                    print("✅ Task completed successfully!")
                    print("🎉 No 'Event loop is closed' errors detected!")
                    return True
                elif status in ["failed", "error"]:
                    print("❌ Task failed")
                    error_msg = progress.get("error_message", "Unknown error")
                    print(f"💥 Error: {error_msg}")

                    # Check if it's an event loop error
                    if "Event loop is closed" in error_msg:
                        print("🚨 EVENT LOOP ERROR DETECTED - Fix did not work!")
                        return False
                    else:
                        print(
                            "ℹ️  Task failed for other reasons (not event loop related)"
                        )
                        return False

            elif response.status_code == 404:
                print("⏳ Task not found yet, waiting...")
            else:
                print(f"⚠️  Progress check returned status {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Progress check failed: {e}")

        time.sleep(check_interval)

    print(f"⏰ Timeout after {max_wait_minutes} minutes")
    return False


def main():
    """Main test function."""
    print("🚀 Starting Newsletter Generation Test")
    print("🎯 Goal: Validate that 'Event loop is closed' error is fixed")
    print()

    # Step 1: Trigger newsletter generation
    task_id = test_newsletter_generation()

    if task_id:
        # Step 2: Monitor progress
        success = monitor_task_progress(task_id, max_wait_minutes=15)

        print("\n" + "=" * 70)
        if success:
            print("🎉 VALIDATION SUCCESSFUL!")
            print("✅ Newsletter generation completed without event loop errors")
            print("✅ Priority 1: Event Loop Issue is RESOLVED")
        else:
            print("❌ VALIDATION FAILED")
            print("🔍 Check logs for details on what went wrong")
    else:
        print("❌ Could not start newsletter generation task")

    return task_id is not None


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
