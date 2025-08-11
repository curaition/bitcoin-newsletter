# Railway Deployment Guide

## Overview

This guide covers deploying the Bitcoin Newsletter system to Railway with a multi-service architecture including web service, Celery worker, beat scheduler, and Redis.

## Prerequisites

### 1. GitHub Repository Setup
- ✅ Repository created: `curaition/bitcoin-newsletter`
- ⏳ **NEEDED**: Add collaborator access for deployment
- ⏳ **NEEDED**: Push code to GitHub repository

### 2. Railway Project
- ✅ Project exists: `bitcoin-newsletter` (ID: f672d6bf-ac6b-4d62-9a38-158919110629)
- ✅ Redis service already configured
- ✅ Production environment ready

## Deployment Architecture

### Services Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Service   │    │ Celery Worker   │    │  Celery Beat    │
│   (FastAPI)     │    │   (Tasks)       │    │ (Scheduler)     │
│   Port: 8000    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │     Redis       │    │   Neon DB       │
                    │   (Broker)      │    │ (PostgreSQL)    │
                    └─────────────────┘    └─────────────────┘
```

### Service Configuration

#### 1. Web Service (FastAPI)
- **Purpose**: HTTP API and health monitoring
- **Port**: 8000 (public)
- **Health Check**: `/health`
- **Start Command**: `uv run uvicorn crypto_newsletter.web.main:app --host 0.0.0.0 --port $PORT --workers 1`

#### 2. Worker Service (Celery)
- **Purpose**: Background task processing
- **Queues**: default, ingestion, monitoring, maintenance
- **Start Command**: `uv run celery -A crypto_newsletter.shared.celery.app worker --loglevel=INFO --concurrency=2 --queues=default,ingestion,monitoring,maintenance`

#### 3. Beat Service (Celery Scheduler)
- **Purpose**: Periodic task scheduling
- **Schedule**: Article ingestion every 4 hours, health checks every 5 minutes
- **Start Command**: `uv run celery -A crypto_newsletter.shared.celery.app beat --loglevel=INFO --pidfile=`

#### 4. Redis Service
- **Purpose**: Message broker and result backend
- **Status**: ✅ Already configured
- **Connection**: Available via `${{Redis.REDIS_URL}}`

## Environment Variables

### Shared Variables (All Services)
```bash
PYTHONPATH=/app/src
UV_SYSTEM_PYTHON=1
PYTHONFAULTHANDLER=1
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
DATABASE_URL=${{Neon.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
RAILWAY_ENVIRONMENT=production
```

### Service-Specific Variables
```bash
# Web Service
SERVICE_TYPE=web
PORT=8000

# Worker Service  
SERVICE_TYPE=worker

# Beat Service
SERVICE_TYPE=beat
```

## Deployment Steps

### Step 1: Repository Connection
```bash
# Connect local repository to GitHub
git remote add origin https://github.com/curaition/bitcoin-newsletter.git
git branch -M main
git push -u origin main
```

### Step 2: Railway Service Configuration
The following Railway services are already created and need to be connected to the repository:

1. **Web Service** (ID: 2ca4f993-52fe-40b8-8056-eddfebdadac1)
2. **Worker Service** (ID: 759ee78c-712e-4709-bff4-5871a7f93892)  
3. **Beat Service** (ID: a4cdedf4-812f-4b3d-bd56-ab0f47e95fdb)

### Step 3: Environment Variables Setup
All environment variables are configured and ready to be applied once repository access is available.

### Step 4: Database Migration
```bash
# Database migrations will run automatically during deployment
# via the build command: uv run alembic upgrade head
```

## Health Monitoring

### Railway Health Checks
- **Path**: `/health`
- **Timeout**: 100 seconds
- **Interval**: 30 seconds
- **Retries**: 3

### Available Health Endpoints
- `/health/` - Basic health for load balancers
- `/health/ready` - Readiness probe with database check
- `/health/live` - Liveness probe for containers
- `/health/detailed` - Comprehensive system health
- `/health/metrics` - System metrics and statistics

## Monitoring and Management

### API Endpoints
- **Admin Dashboard**: `/admin/status`
- **Task Management**: `/admin/tasks/*`
- **Public API**: `/api/articles`, `/api/stats`
- **Documentation**: `/docs` (development only)

### CLI Management
```bash
# Check deployment status
railway status

# View logs
railway logs --service web
railway logs --service worker
railway logs --service beat

# Connect to services
railway shell --service web
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
- Check logs: `railway logs --service [service-name]`
- Verify environment variables are set
- Ensure database migrations completed

#### 2. Database Connection Issues
- Verify `DATABASE_URL` is correctly set
- Check Neon database is accessible
- Run health check: `GET /health/ready`

#### 3. Celery Tasks Not Processing
- Check worker service logs
- Verify Redis connection: `REDIS_URL`
- Check beat scheduler is running
- Monitor tasks: `GET /admin/tasks/active`

#### 4. Health Check Failures
- Check `/health/detailed` for specific component issues
- Verify all environment variables are set
- Check service startup logs

## Next Steps After Repository Access

1. **Connect services to GitHub repository**
2. **Deploy all services simultaneously**
3. **Verify health checks are passing**
4. **Test article ingestion pipeline**
5. **Monitor system performance**

## Current Status

- ✅ Railway project configured
- ✅ All services created and configured
- ✅ Environment variables prepared
- ✅ Health monitoring implemented
- ⏳ **WAITING**: GitHub repository access for deployment

Once repository access is granted, the deployment can be completed in minutes!
