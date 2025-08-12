# Celery Task Queue Setup - Railway Cloud Infrastructure

This document describes the **NEW RAILWAY-BASED** Celery task queue configuration for automated article ingestion and background processing.

## Overview

The Bitcoin Newsletter now uses **Railway's cloud infrastructure** for Celery processing:
- **Railway Worker**: Processes background tasks in the cloud
- **Railway Beat**: Schedules tasks every 4 hours in the cloud
- **Railway Redis**: Message broker in the cloud
- **Local Development**: Web service runs locally with hot reload
- **Shared Database**: Neon PostgreSQL accessible from both environments

## New Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL DEVELOPMENT                            │
│  ┌─────────────────┐                                           │
│  │   Web Service   │  ← You develop here                       │
│  │   (FastAPI)     │  ← Submit tasks to Railway                │
│  │ localhost:8000  │                                           │
│  └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
           │ railway run (environment variables)
           │
┌─────────────────────────────────────────────────────────────────┐
│                  RAILWAY CLOUD INFRASTRUCTURE                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   Celery Beat   │    │  Celery Worker  │    │    Redis    │ │
│  │   (Scheduler)   │───▶│  (Processor)    │◀──▶│  (Broker)   │ │
│  │                 │    │                 │    │             │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │                       │                       │
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Periodic Tasks │    │ Background Jobs │    │ Task Results    │
│  - Ingestion    │    │ - API Calls     │    │ - Success/Fail  │
│  - Health Check │    │ - DB Operations │    │ - Metrics       │
│  - Cleanup      │    │ - Processing    │    │ - Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   │
                      ┌─────────────────┐
                      │   Neon DB       │
                      │ (PostgreSQL)    │
                      │   (Shared)      │
                      └─────────────────┘
```

## Railway Infrastructure

### Railway Project: `proactive-alignment`
- **Project ID**: `6115f406-107e-45c3-85d4-d720c3638053`
- **Worker Service**: `celery -A main.app worker --concurrency=1 -l INFO`
- **Beat Service**: `celery -A main.app beat -l INFO`
- **Redis Service**: Managed by Railway
- **Environment**: All variables configured

### Celery App Compatibility
The `main.py` file provides compatibility between Railway's expected `main.app` and our project structure:

```python
# main.py - Railway entry point
from crypto_newsletter.shared.celery.app import celery_app
app = celery_app  # Expose for Railway services
```

### Local Development Integration
```bash
# Start local development with Railway infrastructure
./scripts/dev-railway.sh

# Test tasks using Railway infrastructure
./scripts/test-railway-tasks.sh
```

## Scheduled Tasks

### 1. Article Ingestion (`ingest-articles-every-4-hours`)
- **Schedule**: Every 4 hours (0, 4, 8, 12, 16, 20 UTC)
- **Purpose**: Fetch and process new articles from CoinDesk API
- **Execution**: Railway Worker Service
- **Storage**: Neon PostgreSQL Database
- **Retry**: 3 attempts with exponential backoff
- **Timeout**: 30 minutes

### 2. Health Monitoring (`health-check-every-5-minutes`)
- **Schedule**: Every 5 minutes
- **Purpose**: Monitor API and database connectivity
- **Execution**: Railway Worker Service
- **Monitoring**: Railway logs and dashboard
- **Retry**: 1 attempt
- **Timeout**: 5 minutes

### 3. Article Cleanup (`cleanup-old-articles-daily`)
- **Schedule**: Daily at 2:00 AM UTC
- **Purpose**: Mark articles older than 30 days as DELETED
- **Execution**: Railway Worker Service
- **Database**: Neon PostgreSQL cleanup
- **Retry**: 2 attempts
- **Timeout**: 30 minutes

## Development Setup

### 1. Start Redis
```bash
# Option 1: Using our script
./scripts/start-redis.sh

# Option 2: Manual start
redis-server --daemonize yes --port 6379

# Option 3: Docker
docker run -d -p 6379:6379 redis:alpine
```

### 2. Start Celery Worker
```bash
# Terminal 1: Start worker
python -m crypto_newsletter.cli.main worker

# Or directly with Celery
celery -A crypto_newsletter.shared.celery.app worker --loglevel=INFO
```

### 3. Start Celery Beat (Optional for development)
```bash
# Terminal 2: Start scheduler
python -m crypto_newsletter.cli.main beat

# Or directly with Celery
celery -A crypto_newsletter.shared.celery.app beat --loglevel=INFO
```

### 4. Start Flower Monitoring (Optional)
```bash
# Terminal 3: Start monitoring
python -m crypto_newsletter.cli.main flower

# Access at: http://localhost:5555
```

## CLI Commands

### Task Management
```bash
# Schedule immediate ingestion
python -m crypto_newsletter.cli.main schedule-ingest --limit 5 --hours 4

# Check task status
python -m crypto_newsletter.cli.main task-status <task-id>

# Manual ingestion (synchronous)
python -m crypto_newsletter.cli.main ingest --limit 5 --hours 4
```

### Service Management
```bash
# Start worker
python -m crypto_newsletter.cli.main worker --concurrency 2

# Start beat scheduler
python -m crypto_newsletter.cli.main beat

# Start Flower monitoring
python -m crypto_newsletter.cli.main flower --port 5555
```

## Production Deployment

### Railway Configuration

The project includes separate Docker containers for:
- **Celery Worker**: `docker/celery-worker.Dockerfile`
- **Celery Beat**: `docker/celery-beat.Dockerfile`

### Environment Variables
```bash
# Required for production
REDIS_URL=redis://redis-service:6379/0
CELERY_BROKER_URL=redis://redis-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-service:6379/1
ENABLE_CELERY=true

# Database (already configured)
DATABASE_URL=postgresql://...

# API keys (already configured)
COINDESK_API_KEY=...
```

### Railway Services
1. **Redis Service**: Deploy Redis for message broker
2. **Celery Worker Service**: Process background tasks
3. **Celery Beat Service**: Schedule periodic tasks
4. **FastAPI Service**: Web API (next task)

## Monitoring and Debugging

### Flower Dashboard
- **URL**: http://localhost:5555 (development)
- **Features**: Task monitoring, worker stats, queue inspection
- **Authentication**: admin/admin (basic auth)

### Redis Monitoring
```bash
# Monitor Redis commands
redis-cli monitor

# Check queue lengths
redis-cli llen celery

# View task results
redis-cli keys "celery-task-meta-*"
```

### Logs
- **Worker logs**: Celery worker output
- **Beat logs**: Scheduler output
- **Application logs**: Loguru logs in application code

## Task Configuration

### Queue Routing
- `default`: General tasks
- `ingestion`: Article processing tasks
- `monitoring`: Health checks and monitoring
- `maintenance`: Cleanup and maintenance tasks

### Retry Policies
- **Ingestion**: 3 retries, exponential backoff (5min → 10min → 20min)
- **Health Check**: 1 retry, 10 minute delay
- **Cleanup**: 2 retries, 10 minute delay

### Resource Limits
- **Time Limit**: 30 minutes per task
- **Soft Time Limit**: 25 minutes (graceful shutdown)
- **Concurrency**: 2 workers (adjustable for Railway)
- **Memory**: Optimized for Railway's resource constraints

## Testing

```bash
# Run Celery integration tests
pytest tests/integration/test_celery_tasks.py -v

# Test task execution
python -c "from crypto_newsletter.core.scheduling.tasks import manual_ingest; print(manual_ingest(limit=1))"
```

## Troubleshooting

### Common Issues
1. **Redis Connection**: Ensure Redis is running on port 6379
2. **Import Errors**: Check PYTHONPATH and virtual environment
3. **Task Failures**: Check worker logs and task retry settings
4. **Memory Issues**: Adjust worker concurrency for Railway limits

### Debug Commands
```bash
# Check Celery configuration
python -c "from crypto_newsletter.shared.celery.app import celery_app; print(celery_app.conf)"

# Test Redis connection
redis-cli ping

# List active tasks
celery -A crypto_newsletter.shared.celery.app inspect active
```
