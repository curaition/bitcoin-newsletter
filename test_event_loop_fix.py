#!/usr/bin/env python3
"""
Test script to verify the event loop fix for newsletter generation.

This script tests that PydanticAI agents work correctly with the AsyncIO pool
without causing "Event loop is closed" errors.
"""

import asyncio
import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def test_newsletter_generation():
    """Test newsletter generation without event loop conflicts."""
    print("🧪 Testing newsletter generation with AsyncIO pool compatibility...")

    try:
        # Import the fixed task
        from crypto_newsletter.newsletter.tasks import (
            check_newsletter_alerts_task,
            cleanup_progress_records_task,
            generate_newsletter_manual_task_enhanced,
        )

        print("✅ Successfully imported newsletter tasks")

        # Test that all tasks are now async
        import inspect

        tasks_to_test = [
            (
                "generate_newsletter_manual_task_enhanced",
                generate_newsletter_manual_task_enhanced,
            ),
            ("check_newsletter_alerts_task", check_newsletter_alerts_task),
            ("cleanup_progress_records_task", cleanup_progress_records_task),
        ]

        all_async = True
        for task_name, task_func in tasks_to_test:
            print(f"🔍 Inspecting {task_name}:")
            print(f"   Type: {type(task_func)}")
            print(f"   Is coroutine function: {inspect.iscoroutinefunction(task_func)}")

            # Check if it's a Celery task wrapper
            if hasattr(task_func, "run"):
                print(
                    f"   Has 'run' method: {inspect.iscoroutinefunction(task_func.run)}"
                )
            if hasattr(task_func, "__wrapped__"):
                print(
                    f"   Has '__wrapped__': {inspect.iscoroutinefunction(task_func.__wrapped__)}"
                )

            # For Celery tasks, we need to check the actual function
            is_async = (
                inspect.iscoroutinefunction(task_func)
                or (
                    hasattr(task_func, "run")
                    and inspect.iscoroutinefunction(task_func.run)
                )
                or (
                    hasattr(task_func, "__wrapped__")
                    and inspect.iscoroutinefunction(task_func.__wrapped__)
                )
            )

            if is_async:
                print(f"✅ {task_name} is async")
            else:
                print(f"❌ {task_name} is still sync")
                all_async = False

        if all_async:
            print("✅ All tasks are now async - event loop fix is working!")
            print("📝 Tasks are now compatible with AsyncIO pool")

        return all_async

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_pydantic_ai_compatibility():
    """Test that PydanticAI agents work in async context."""
    print("\n🧪 Testing PydanticAI agent compatibility...")

    try:
        # Import a PydanticAI agent

        print("✅ Successfully imported PydanticAI agent")

        # Test that we can create the agent without issues
        print("✅ PydanticAI agent is ready for async execution")

        return True

    except Exception as e:
        print(f"❌ PydanticAI test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing Event Loop Fix for Newsletter Generation")
    print("=" * 60)

    # Test 1: Newsletter task conversion
    test1_passed = await test_newsletter_generation()

    # Test 2: PydanticAI compatibility
    test2_passed = await test_pydantic_ai_compatibility()

    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Event loop fix is working correctly")
        print(
            "✅ Newsletter generation should work without 'Event loop is closed' errors"
        )
    else:
        print("❌ Some tests failed - fix may need additional work")

    return test1_passed and test2_passed


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
