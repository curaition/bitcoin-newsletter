"""
Minimal Django setup for django-celery-beat scheduler.

This module provides the minimal Django configuration needed to use
django-celery-beat's DatabaseScheduler without a full Django application.
"""

import os
import django
from django.conf import settings
from django.core.management import execute_from_command_line

from crypto_newsletter.shared.config.settings import get_settings


def setup_django():
    """
    Configure Django with minimal settings for django-celery-beat.
    
    This setup only includes what's necessary for the beat scheduler
    to store periodic tasks in the database.
    """
    if settings.configured:
        return
    
    app_settings = get_settings()
    
    # Parse DATABASE_URL for Django format
    database_url = app_settings.database_url

    # Extract database components from URL
    # Format: postgresql://user:password@host:port/database or postgresql+asyncpg://...
    if database_url.startswith('postgresql://') or database_url.startswith('postgresql+asyncpg://'):
        # Remove protocol (handle both formats)
        if database_url.startswith('postgresql+asyncpg://'):
            url_parts = database_url.replace('postgresql+asyncpg://', '')
        else:
            url_parts = database_url.replace('postgresql://', '')
        
        # Split user:password@host:port/database
        if '@' in url_parts:
            auth_part, host_part = url_parts.split('@', 1)
            if ':' in auth_part:
                db_user, db_password = auth_part.split(':', 1)
            else:
                db_user, db_password = auth_part, ''
        else:
            db_user, db_password = '', ''
            host_part = url_parts
        
        # Split host:port/database
        if '/' in host_part:
            host_port, db_name = host_part.split('/', 1)
            # Remove query parameters if present
            if '?' in db_name:
                db_name = db_name.split('?')[0]
        else:
            host_port, db_name = host_part, 'neondb'
        
        # Split host:port
        if ':' in host_port:
            db_host, db_port = host_port.split(':', 1)
        else:
            db_host, db_port = host_port, '5432'
    else:
        # Fallback to environment variables
        db_host = os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('PGPORT', '5432')
        db_name = os.getenv('PGDATABASE', 'neondb')
        db_user = os.getenv('PGUSER', '')
        db_password = os.getenv('PGPASSWORD', '')
    
    # Configure Django with minimal settings
    settings.configure(
        # Database configuration
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
                'OPTIONS': {
                    'sslmode': 'require',  # Required for Neon
                },
            }
        },
        
        # Minimal app configuration
        INSTALLED_APPS=[
            'django_celery_beat',  # Only app we need
        ],
        
        # Timezone settings (match Celery config)
        USE_TZ=True,
        TIME_ZONE='UTC',
        
        # Security (minimal for beat scheduler)
        SECRET_KEY=app_settings.secret_key,
        
        # Disable unnecessary Django features
        USE_I18N=False,
        USE_L10N=False,
        
        # Logging configuration
        LOGGING={
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                },
            },
            'loggers': {
                'django_celery_beat': {
                    'handlers': ['console'],
                    'level': 'INFO',
                },
            },
        },
    )
    
    # Initialize Django
    django.setup()


def run_django_migrations():
    """
    Run Django migrations to create django-celery-beat tables.
    
    This should be called once during deployment to set up the
    necessary database tables for the beat scheduler.
    """
    setup_django()
    
    # Run migrations for django-celery-beat
    execute_from_command_line([
        'manage.py', 'migrate', 'django_celery_beat', '--verbosity=2'
    ])


def create_periodic_tasks():
    """
    Create periodic tasks in the database.
    
    This function creates the same periodic tasks that are currently
    defined in the Celery beat_schedule configuration.
    """
    setup_django()
    
    from django_celery_beat.models import PeriodicTask, CrontabSchedule
    
    # Create crontab schedules
    every_4_hours, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour='*/4',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )
    
    every_5_minutes, _ = CrontabSchedule.objects.get_or_create(
        minute='*/5',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )
    
    daily_at_2am, _ = CrontabSchedule.objects.get_or_create(
        minute=0,
        hour=2,
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
    )
    
    # Create periodic tasks
    PeriodicTask.objects.get_or_create(
        name='ingest-articles-every-4-hours',
        defaults={
            'crontab': every_4_hours,
            'task': 'crypto_newsletter.core.scheduling.tasks.ingest_articles',
            'kwargs': '{"hours_back": 12}',
            'enabled': True,
        }
    )
    
    PeriodicTask.objects.get_or_create(
        name='health-check-every-5-minutes',
        defaults={
            'crontab': every_5_minutes,
            'task': 'crypto_newsletter.core.scheduling.tasks.health_check',
            'enabled': True,
        }
    )
    
    PeriodicTask.objects.get_or_create(
        name='cleanup-old-articles-daily',
        defaults={
            'crontab': daily_at_2am,
            'task': 'crypto_newsletter.core.scheduling.tasks.cleanup_old_articles',
            'enabled': True,
        }
    )
    
    print("✅ Periodic tasks created successfully!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'migrate':
            run_django_migrations()
        elif command == 'create-tasks':
            create_periodic_tasks()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: migrate, create-tasks")
    else:
        print("Usage: python django_minimal.py [migrate|create-tasks]")
