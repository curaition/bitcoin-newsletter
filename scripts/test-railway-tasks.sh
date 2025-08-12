#!/bin/bash

# Bitcoin Newsletter - Railway Task Testing Script
# This script tests task execution using Railway's cloud infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test task execution
test_health_check() {
    print_status "Testing health check task..."
    railway run python -c "
from crypto_newsletter.core.scheduling.tasks import health_check
result = health_check.delay()
print(f'Health check task ID: {result.id}')
print('Task submitted to Railway worker!')
"
}

test_article_ingestion() {
    print_status "Testing article ingestion task..."
    railway run python -c "
from crypto_newsletter.core.scheduling.tasks import ingest_articles
result = ingest_articles.delay()
print(f'Article ingestion task ID: {result.id}')
print('Task submitted to Railway worker!')
"
}

test_database_connection() {
    print_status "Testing database connection..."
    railway run python -c "
import sys
sys.path.insert(0, 'src')
import asyncio

from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Article
from sqlalchemy import select

async def test_db():
    try:
        async with get_db_session() as session:
            result = await session.execute(select(Article))
            articles = result.scalars().all()
            print(f'✅ Database connection successful!')
            print(f'📊 Articles in database: {len(articles)}')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

asyncio.run(test_db())
"
}

show_celery_status() {
    print_status "Checking Celery app configuration..."
    railway run python -c "
from main import app
print(f'🚀 Celery App: {app}')
print(f'📋 Registered tasks: {len(app.tasks)} tasks')
print(f'🔧 Broker URL: {app.conf.broker_url}')
print(f'📊 Result Backend: {app.conf.result_backend}')
print()
print('📋 Available tasks:')
for task_name in sorted(app.tasks.keys()):
    if not task_name.startswith('celery.'):
        print(f'  - {task_name}')
"
}

show_beat_schedule() {
    print_status "Checking beat schedule..."
    railway run python -c "
from main import app
if app.conf.beat_schedule:
    print('⏰ Scheduled Tasks:')
    for name, config in app.conf.beat_schedule.items():
        print(f'  - {name}: {config[\"task\"]} ({config[\"schedule\"]})')
else:
    print('⚠️  No beat schedule configured')
"
}

# Main execution
main() {
    echo ""
    print_status "🧪 Bitcoin Newsletter - Railway Task Testing"
    echo ""
    
    show_celery_status
    echo ""
    show_beat_schedule
    echo ""
    test_database_connection
    echo ""
    test_health_check
    echo ""
    
    read -p "Do you want to test article ingestion? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_article_ingestion
    fi
    
    echo ""
    print_success "Task testing completed!"
    print_status "Check Railway logs to see task execution details"
}

# Run main function
main "$@"
