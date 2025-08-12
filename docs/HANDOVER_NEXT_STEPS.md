# Bitcoin Newsletter - Railway Development Environment

## 🎯 Current Status (As of 2025-08-12)

### ✅ NEW SIMPLIFIED DEPLOYMENT COMPLETED
- **Railway Project**: `proactive-alignment` (ID: 6115f406-107e-45c3-85d4-d720c3638053)
- **Celery Worker**: ✅ Running and processing tasks on Railway
- **Celery Beat**: ✅ Running and scheduling tasks on Railway
- **Redis Service**: ✅ Connected and operational on Railway
- **Neon Database**: ✅ Connected and operational (shared)
- **Environment Variables**: ✅ All configured in Railway
- **Local Development**: ✅ Ready for hybrid development

### 🚀 Development Approach
- **Local Web Service**: FastAPI with hot reload
- **Cloud Task Processing**: Worker and Beat on Railway
- **Shared Database**: Neon PostgreSQL
- **Simplified Workflow**: No complex multi-service management

---

## Quick Start Guide

### 1. Setup Railway CLI
```bash
# Install Railway CLI
curl -fsSL https://railway.com/install.sh | sh

# Authenticate
railway login

# Link to the new project
railway link -p 6115f406-107e-45c3-85d4-d720c3638053

# Verify connection
railway status
```

### 2. Start Local Development
```bash
# Start local web service with Railway infrastructure
./scripts/dev-railway.sh
```

Your development server will be available at: `http://localhost:8000`

### 3. Test Task Execution
```bash
# Test tasks using Railway infrastructure
./scripts/test-railway-tasks.sh
```

This will test:
- Database connection
- Health check tasks
- Article ingestion (optional)

## Development Workflow

### Daily Development Process
1. **Start Local Development**: `./scripts/dev-railway.sh`
2. **Develop Web Features**: Edit code with hot reload at localhost:8000
3. **Test Tasks**: Use `./scripts/test-railway-tasks.sh`
4. **Monitor**: Check Railway dashboard for worker/beat logs

### Task Processing Flow
```
Local Web Service → Submit Task → Railway Worker → Process Task → Store in Neon DB
     ↑                                                                    ↓
   You develop here                                            Data available locally
```
    articles = session.query(Article).limit(5).all()
    print(f'Total articles: {len(articles)}')
    for article in articles:
        print(f'- {article.title} ({article.created_at})')
"
```

#### 2.3 Test API Endpoints
```bash
# Test article retrieval via API
curl -X GET "https://[your-web-service-url]/api/articles?limit=5"

# Test health endpoint with database check
curl -X GET "https://[your-web-service-url]/health/ready"
```

### Expected Results
- Task executes without errors
- Articles are stored in Neon database
- API endpoints return article data
- Health checks pass

### Troubleshooting
- **Task fails**: Check Celery worker logs: `railway logs --service celery-worker`
- **No articles**: Verify CoinDesk API key is set: `COINDESK_API_KEY`
- **Database errors**: Check Neon connection: `DATABASE_URL`

---

## Step 3: Clean Up Debug Code

### Objective
Remove temporary debug code added during deployment troubleshooting.

### Files to Clean Up

#### 3.1 Remove Redis Import Debug Code
**File**: `src/crypto_newsletter/shared/celery/app.py`
**Lines to remove/simplify**:
```python
# REMOVE: Verbose error handling and print statements
# KEEP: Essential Redis import for Kombu compatibility
```

#### 3.2 Remove idna Encoding Debug Code
**File**: `src/crypto_newsletter/shared/celery/app.py`
**Lines to clean up**:
```python
# SIMPLIFY: Keep essential idna import, remove verbose error handling
# KEEP: Core encoding registration for Railway compatibility
```

#### 3.3 Simplified Clean Version
Replace the debug imports with:
```python
"""Celery application configuration and setup."""

# Essential imports for Railway compatibility
import redis  # Required before Kombu imports
import encodings.idna  # Required for Railway containers

from celery import Celery
from celery.schedules import crontab
from kombu import Queue
```

### Testing After Cleanup
1. Deploy changes to Railway
2. Verify Celery worker starts successfully
3. Test task execution still works
4. Monitor for 30 minutes to ensure stability

---

## Step 4: Add Celery Beat Service

### Objective
Deploy the Celery Beat scheduler for automated periodic tasks.

### 4.1 Create Celery Beat Service on Railway

#### Service Configuration
```yaml
Service Name: celery-beat
Build Command: uv sync --frozen
Start Command: uv run celery -A crypto_newsletter.shared.celery.app beat --loglevel=INFO --pidfile= --uid=1000
```

#### Environment Variables
```bash
# Copy all variables from celery-worker service
PYTHONPATH=/app/src
UV_SYSTEM_PYTHON=1
PYTHONFAULTHANDLER=1
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
DATABASE_URL=${{Neon.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
RAILWAY_ENVIRONMENT=production
SERVICE_TYPE=beat
```

### 4.2 Deployment Steps
1. **Create Service**: Use Railway dashboard or CLI
2. **Connect Repository**: Link to `curaition/bitcoin-newsletter`
3. **Set Environment Variables**: Copy from worker service
4. **Deploy**: Trigger initial deployment
5. **Monitor Logs**: Check for successful startup

### 4.3 Expected Beat Schedule
```
- Article Ingestion: Every 4 hours
- Health Checks: Every 5 minutes  
- Cleanup Tasks: Daily at 2 AM UTC
```

### 4.4 Verification
```bash
# Check beat service logs
railway logs --service celery-beat

# Look for schedule registration messages
# Expected: "Scheduler: Sending due task..."
```

---

## Step 5: Update Documentation After Beat Deployment

### Objective
Update deployment documentation to reflect complete system status.

### Files to Update

#### 5.1 Update `docs/RAILWAY_DEPLOYMENT.md`
- Change Beat service status from "⏳ Pending" to "✅ Deployed"
- Add Beat service deployment details
- Update current status section

#### 5.2 Update Service Configuration Section
```markdown
#### 3. Beat Service (Celery Scheduler) ✅ DEPLOYED
- **Purpose**: Periodic task scheduling
- **Schedule**: Article ingestion every 4 hours, health checks every 5 minutes
- **Start Command**: `uv run celery -A crypto_newsletter.shared.celery.app beat --loglevel=INFO --pidfile= --uid=1000`
- **Status**: ✅ Running and scheduling tasks
```

---

## Step 6: Clean Up Celery Beat Debug Code

### Objective
Remove any debug code added during Beat service deployment.

### Process
1. **Review Beat Logs**: Check for any debug output
2. **Remove Debug Prints**: Clean up any temporary logging
3. **Test Deployment**: Ensure Beat service still works after cleanup
4. **Monitor Stability**: Verify scheduled tasks execute properly

---

## Step 7: Performance Monitoring (24 Hours)

### Objective
Monitor system performance and stability over 24 hours.

### 7.1 Monitoring Checklist

#### Service Health
- [ ] Web service uptime and response times
- [ ] Celery worker task processing rates
- [ ] Celery beat schedule execution
- [ ] Redis connection stability
- [ ] Neon database performance

#### Key Metrics to Track
```bash
# Service status checks (every hour)
railway status

# Log monitoring
railway logs --service web --tail
railway logs --service celery-worker --tail  
railway logs --service celery-beat --tail

# Health endpoint monitoring
curl -X GET "https://[web-service-url]/health/detailed"
```

#### Performance Indicators
- **Task Success Rate**: >95%
- **API Response Time**: <500ms
- **Database Query Time**: <100ms
- **Memory Usage**: <80% of allocated
- **Error Rate**: <1%

### 7.2 Monitoring Tools

#### Railway Dashboard
- Service metrics and logs
- Resource usage graphs
- Deployment history

#### Health Endpoints
- `/health/detailed` - Comprehensive system status
- `/health/metrics` - Performance metrics
- `/admin/tasks/active` - Active task monitoring

#### Database Monitoring
- Neon dashboard for query performance
- Connection pool usage
- Storage utilization

### 7.3 Alert Conditions
Monitor for:
- Service crashes or restarts
- High error rates in logs
- Database connection failures
- Task processing delays
- Memory or CPU spikes

---

## 🚨 Emergency Contacts & Resources

### Railway Project Details
- **Project ID**: `f672d6bf-ac6b-4d62-9a38-158919110629`
- **Project Name**: `bitcoin-newsletter`
- **Environment**: `production`

### Service IDs
- **Web Service**: Check Railway dashboard
- **Celery Worker**: `b8724d3a-07ee-44d9-b771-7b50d70c829d`
- **Redis Service**: Check Railway dashboard

### Key Files Modified
- `src/crypto_newsletter/shared/celery/app.py` - Celery configuration
- `pyproject.toml` - Dependencies (Redis, idna)
- `docs/RAILWAY_DEPLOYMENT.md` - Deployment documentation

### Rollback Procedure
If issues arise:
1. Check recent commits: `git log --oneline -10`
2. Identify last working commit
3. Revert: `git revert [commit-hash]`
4. Push: `git push origin main`
5. Monitor Railway auto-deployment

---

## ✅ Success Criteria

### Step 2 Complete When:
- [ ] Tasks execute successfully
- [ ] Articles stored in database
- [ ] API endpoints return data

### Step 4 Complete When:
- [ ] Beat service deployed and running
- [ ] Scheduled tasks executing on time
- [ ] No errors in beat logs

### Step 7 Complete When:
- [ ] 24-hour monitoring completed
- [ ] Performance metrics within targets
- [ ] System stability confirmed
- [ ] Documentation updated with final status

**System is production-ready when all steps are complete!** 🎉

---

## 📋 Quick Reference Commands

### Railway CLI Commands
```bash
# Check all services status
railway status

# View logs for specific service
railway logs --service web
railway logs --service celery-worker
railway logs --service celery-beat

# Connect to service shell
railway shell --service web

# Deploy specific service
railway up --service celery-beat
```

### Database Commands
```bash
# Connect to Neon database
railway connect Neon

# Run database migrations
uv run alembic upgrade head

# Check database connection
python -c "from crypto_newsletter.shared.database.connection import get_db_session; print('DB Connected:', bool(get_db_session()))"
```

### Celery Commands
```bash
# Check active tasks
python -c "from crypto_newsletter.shared.celery.app import celery_app; print(celery_app.control.active())"

# Inspect registered tasks
python -c "from crypto_newsletter.shared.celery.app import celery_app; print(list(celery_app.tasks.keys()))"

# Test task execution
python -c "from crypto_newsletter.core.scheduling.tasks import health_check; result = health_check.delay(); print(f'Task: {result.id}, Status: {result.status}')"
```

---

## 🔍 Debugging Guide

### Common Issues and Solutions

#### Celery Worker Not Processing Tasks
1. **Check Redis Connection**:
   ```bash
   railway logs --service celery-worker | grep "Connected to redis"
   ```

2. **Verify Task Registration**:
   ```bash
   railway shell --service celery-worker
   python -c "from crypto_newsletter.shared.celery.app import celery_app; print(celery_app.tasks)"
   ```

3. **Check Queue Status**:
   ```bash
   python -c "from crypto_newsletter.shared.celery.app import celery_app; print(celery_app.control.inspect().active_queues())"
   ```

#### Beat Service Not Scheduling
1. **Check Beat Logs**:
   ```bash
   railway logs --service celery-beat | grep "Scheduler"
   ```

2. **Verify Schedule Configuration**:
   ```bash
   python -c "from crypto_newsletter.shared.celery.app import celery_app; print(celery_app.conf.beat_schedule)"
   ```

#### Database Connection Issues
1. **Test Connection**:
   ```bash
   python -c "from crypto_newsletter.shared.database.connection import test_connection; test_connection()"
   ```

2. **Check Environment Variables**:
   ```bash
   echo $DATABASE_URL | head -c 50  # Show first 50 chars
   ```

---

## 📊 Performance Benchmarks

### Expected Performance Metrics

#### API Response Times
- `/health`: <100ms
- `/api/articles`: <300ms
- `/admin/status`: <500ms

#### Task Processing
- Article ingestion: 2-5 minutes per batch
- Health check: <10 seconds
- Cleanup tasks: <30 seconds

#### Resource Usage
- **Memory**: <512MB per service
- **CPU**: <50% average usage
- **Database**: <100 concurrent connections

### Monitoring Queries
```sql
-- Check recent articles
SELECT title, created_at FROM articles ORDER BY created_at DESC LIMIT 10;

-- Check task execution history
SELECT * FROM celery_taskmeta ORDER BY date_done DESC LIMIT 10;

-- Database performance
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

---

## 🎯 Final Checklist

### Before Handover Complete
- [ ] All services running stable for 24+ hours
- [ ] Task execution verified and working
- [ ] Database storage confirmed
- [ ] Beat scheduling operational
- [ ] Performance metrics within targets
- [ ] Documentation updated
- [ ] Debug code cleaned up
- [ ] Emergency procedures tested

### Handover Package Includes
- [ ] Updated `RAILWAY_DEPLOYMENT.md`
- [ ] This handover document
- [ ] Performance monitoring results
- [ ] Any issues encountered and resolved
- [ ] Recommendations for ongoing maintenance

**The system is ready for production use!** 🚀
