#!/usr/bin/env python3
"""
Celery entry point for Railway Celery services.

This module provides compatibility between Railway's expected 'main.app'
and our project's Celery app located at 'crypto_newsletter.shared.celery.app'.

Railway worker/beat services expect to import 'celery_main.app', so this file exposes our
configured Celery application instance.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import our configured Celery app
from crypto_newsletter.shared.celery.app import celery_app

# Expose the app for Railway services
# Railway worker will use: celery -A main.app worker
# Railway beat will use: celery -A main.app beat
app = celery_app

# Ensure all tasks are discovered and registered
# This is important for Railway services to find all tasks
from crypto_newsletter.core.scheduling import tasks  # noqa: F401

if __name__ == "__main__":
    # This allows running the app directly for testing
    print("🚀 Bitcoin Newsletter Celery App")
    print(f"📋 Registered tasks: {list(app.tasks.keys())}")
    print(f"🔧 Broker URL: {app.conf.broker_url}")
    print(f"📊 Result Backend: {app.conf.result_backend}")
    
    # Print task schedule if beat is configured
    if app.conf.beat_schedule:
        print("\n⏰ Scheduled Tasks:")
        for name, config in app.conf.beat_schedule.items():
            print(f"  - {name}: {config['task']} ({config['schedule']})")
