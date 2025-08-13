# ⚠️ DEPRECATED - Railway Development Guide

## 🔄 Migration Notice

**This document is deprecated.** The Bitcoin Newsletter has been successfully migrated from Railway to Render.

**👉 See current deployment status: [Render Deployment Success](RENDER_DEPLOYMENT_SUCCESS.md)**

---

## Historical Railway Development (Deprecated)

This guide was used for Railway-based development but has been superseded by our successful Render deployment.

## Overview

### What Changed
- ❌ **Old**: Complex multi-service Railway deployment
- ✅ **New**: Hybrid local + cloud development
- ✅ **Benefits**: Faster development, simpler deployment, cost-effective

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL DEVELOPMENT                            │
│  ┌─────────────────┐                                           │
│  │   Web Service   │  ← You develop here with hot reload       │
│  │   (FastAPI)     │                                           │
│  │ localhost:8000  │                                           │
│  └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
           │ Uses Railway environment variables
           │
┌─────────────────────────────────────────────────────────────────┐
│                  RAILWAY CLOUD INFRASTRUCTURE                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Celery Worker   │  │  Celery Beat    │  │     Redis       │ │
│  │   (Tasks)       │  │ (Scheduler)     │  │   (Broker)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │ Shared database connection
           │
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  ┌─────────────────┐                    ┌─────────────────┐     │
│  │   Neon DB       │                    │  CoinDesk API   │     │
│  │ (PostgreSQL)    │                    │                 │     │
│  └─────────────────┘                    └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Railway Project Details

### Project Information
- **Name**: `proactive-alignment`
- **ID**: `6115f406-107e-45c3-85d4-d720c3638053`
- **Services**: Worker, Beat, Redis (all running ✅)

### Active Services
- **Celery Worker**: Processing background tasks
- **Celery Beat**: Scheduling tasks every 4 hours
- **Redis**: Message broker for task queue
- **Environment Variables**: Fully configured

## Quick Start

### 1. First-Time Setup
```bash
# Install Railway CLI
curl -fsSL https://railway.com/install.sh | sh

# Authenticate
railway login

# Link to project
railway link -p 6115f406-107e-45c3-85d4-d720c3638053

# Verify connection
railway status
```

### 2. Daily Development
```bash
# Start local development with Railway infrastructure
./scripts/dev-railway.sh
```

Your web service will be available at: `http://localhost:8000`

### 3. Test Tasks
```bash
# Test task execution using Railway infrastructure
./scripts/test-railway-tasks.sh
```

## Development Workflow

### Local Web Development
- **FastAPI** runs locally with hot reload
- **Environment variables** from Railway via `railway run`
- **Database access** to shared Neon PostgreSQL
- **Task submission** to Railway worker

### Background Task Processing
- **Tasks executed** on Railway worker
- **Scheduled tasks** via Railway beat service
- **Results stored** in shared Neon database
- **Monitoring** via Railway dashboard

### Benefits
1. **Fast Development**: Local web service with hot reload
2. **No Local Infrastructure**: No Redis, worker, or beat to manage
3. **Cloud Processing**: Reliable task execution on Railway
4. **Shared Database**: Consistent data between local and cloud
5. **Cost Effective**: Only pay for Railway infrastructure you use

## Environment Variables

All environment variables are configured in Railway and automatically available via `railway run`:

```bash
# Database
DATABASE_URL=postgresql://neondb_owner:...

# API Keys
COINDESK_API_KEY=346bed562339e612d8c119b80e25f162386d81bdbe323f381a85eab2f0cb74fb

# Python Configuration
PYTHONPATH=/app/src
UV_SYSTEM_PYTHON=1
PYTHONFAULTHANDLER=1
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Redis (automatically provided)
REDIS_URL=${{Redis.REDIS_URL}}
```

## Task Management

### Available Tasks
- **Article Ingestion**: Runs every 4 hours via beat scheduler
- **Health Checks**: Runs every 5 minutes
- **Database Cleanup**: Daily maintenance tasks

### Task Testing
```bash
# Test individual tasks
railway run python -c "
from crypto_newsletter.core.scheduling.tasks import health_check
result = health_check.delay()
print(f'Task ID: {result.id}')
"

# Check database
railway run python -c "
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.core.models.models import Article
with get_db_session() as session:
    count = session.query(Article).count()
    print(f'Articles: {count}')
"
```

## Monitoring

### Railway Dashboard
- Monitor worker and beat service logs
- Check service health and resource usage
- View environment variables

### Local Development
- Web service logs in your terminal
- FastAPI automatic reload on code changes
- Direct database access for debugging

### Database Monitoring
- Neon dashboard for database metrics
- Direct SQL queries via Railway environment

## Troubleshooting

### Common Issues

#### Railway CLI Not Found
```bash
# Install Railway CLI
curl -fsSL https://railway.com/install.sh | sh
# OR
npm i -g @railway/cli
```

#### Project Not Linked
```bash
railway link -p 6115f406-107e-45c3-85d4-d720c3638053
```

#### Tasks Not Executing
1. Check Railway worker service logs
2. Verify Redis connection
3. Test task submission locally

#### Database Connection Issues
1. Check DATABASE_URL in Railway variables
2. Verify Neon database is running
3. Test connection via `railway run`

## Next Steps

1. **Start Development**: Use `./scripts/dev-railway.sh`
2. **Test Tasks**: Use `./scripts/test-railway-tasks.sh`
3. **Monitor Progress**: Check Railway dashboard
4. **Deploy Changes**: Push to GitHub (if needed for production)

This new approach eliminates the complexity of managing multiple Railway services while providing a robust development environment!
