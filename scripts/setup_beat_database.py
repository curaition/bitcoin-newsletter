#!/usr/bin/env python3
"""
Setup script for django-celery-beat database tables and periodic tasks.

This script:
1. Sets up Django with minimal configuration
2. Runs migrations to create django-celery-beat tables
3. Creates periodic tasks in the database
4. Verifies the setup

Usage:
    python scripts/setup_beat_database.py
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from crypto_newsletter.shared.django_minimal import (
    setup_django,
    run_django_migrations,
    create_periodic_tasks
)


def main():
    """Main setup function."""
    command = sys.argv[1] if len(sys.argv) > 1 else "full"

    if command == "migrate":
        print("🚀 Running Django migrations...")
        try:
            setup_django()
            run_django_migrations()
            print("✅ Django migrations completed successfully")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            sys.exit(1)

    elif command == "create-tasks":
        print("🚀 Creating periodic tasks...")
        try:
            setup_django()
            create_periodic_tasks()
            print("✅ Periodic tasks created successfully")
        except Exception as e:
            print(f"❌ Task creation failed: {e}")
            sys.exit(1)

    else:
        # Full setup (original behavior)
        print("🚀 Setting up django-celery-beat database...")

        try:
            # Step 1: Setup Django
            print("\n📋 Step 1: Setting up Django configuration...")
            setup_django()
            print("✅ Django configured successfully")

            # Step 2: Run migrations
            print("\n📋 Step 2: Running database migrations...")
            run_django_migrations()
            print("✅ Database migrations completed")

            # Step 3: Create periodic tasks
            print("\n📋 Step 3: Creating periodic tasks...")
            create_periodic_tasks()
            print("✅ Periodic tasks created")

            # Step 4: Verify setup
            print("\n📋 Step 4: Verifying setup...")
            verify_setup()
            print("✅ Setup verification completed")

            print("\n🎉 Django-Celery-Beat setup completed successfully!")
            print("\nNext steps:")
            print("1. Deploy the updated code to Railway")
            print("2. Start the celery-beat service")
            print("3. Monitor the logs to ensure tasks are being scheduled")

        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)


def verify_setup():
    """Verify that the setup was successful."""
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    
    # Check that tables exist and have data
    task_count = PeriodicTask.objects.count()
    schedule_count = CrontabSchedule.objects.count()
    
    print(f"   📊 Created {task_count} periodic tasks")
    print(f"   📊 Created {schedule_count} crontab schedules")
    
    # List the tasks
    print("\n   📋 Periodic tasks:")
    for task in PeriodicTask.objects.all():
        status = "✅ Enabled" if task.enabled else "❌ Disabled"
        print(f"      - {task.name}: {task.task} ({status})")
    
    if task_count == 0:
        raise Exception("No periodic tasks were created")
    
    print("\n   🔍 Database tables created:")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name LIKE 'django_celery_beat_%'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"      - {table[0]}")


if __name__ == '__main__':
    main()
