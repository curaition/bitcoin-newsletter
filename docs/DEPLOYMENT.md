# Deployment Guide

This guide covers deployment procedures for the Bitcoin Newsletter application across different environments.

## Overview

The Bitcoin Newsletter application is deployed on Railway with a multi-service architecture:

- **Web Service**: FastAPI application serving REST API
- **Worker Service**: Celery workers for background processing
- **Beat Service**: Celery beat scheduler for periodic tasks
- **Redis Service**: Message broker and caching layer
- **Database**: Neon PostgreSQL (external service)

## Prerequisites

### Required Tools

1. **Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Git**
   ```bash
   git --version  # Ensure Git is installed
   ```

3. **UV (for local development)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Required Accounts

1. **Railway Account**: https://railway.app
2. **Neon Account**: https://neon.tech
3. **GitHub Account**: For repository hosting

## Environment Configuration

### Environment Variables

**Required Variables:**
```bash
# Application
RAILWAY_ENVIRONMENT=production
SERVICE_TYPE=web  # or worker, beat
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://default:password@host:port

# External APIs
COINDESK_API_KEY=your-coindesk-api-key
COINDESK_BASE_URL=https://data-api.coindesk.com

# Celery
ENABLE_CELERY=true

# Security
SECRET_KEY=your-secret-key

# Logging
LOG_LEVEL=INFO
```

**Optional Variables:**
```bash
# Performance
ARTICLE_RETENTION_HOURS=720  # 30 days
MAX_WORKERS=4

# Monitoring
SENTRY_DSN=your-sentry-dsn
HEALTH_CHECK_INTERVAL=300

# Email (future)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
FROM_EMAIL=newsletter@yourdomain.com
```

## Railway Configuration

### Project Structure

```
railway.toml
├── [build]
├── [deploy]
└── [[services]]
    ├── web
    ├── worker
    ├── beat
    └── redis
```

### Service Configuration

**railway.toml:**
```toml
[build]
builder = "nixpacks"
buildCommand = "uv pip install -e ."

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

# Web Service
[[services]]
name = "web"
source = "."
variables = { SERVICE_TYPE = "web" }

[services.healthcheck]
path = "/health"
interval = 30
timeout = 10
retries = 3

# Worker Service
[[services]]
name = "worker"
source = "."
variables = { SERVICE_TYPE = "worker" }

[services.healthcheck]
command = ["python", "-c", "import redis; r = redis.from_url('$REDIS_URL'); r.ping()"]
interval = 60
timeout = 30
retries = 3

# Beat Service
[[services]]
name = "beat"
source = "."
variables = { SERVICE_TYPE = "beat" }

[services.healthcheck]
command = ["python", "-c", "import redis; r = redis.from_url('$REDIS_URL'); r.ping()"]
interval = 60
timeout = 30
retries = 3

# Redis Service
[[services]]
name = "redis"
image = "redis:7-alpine"

[services.healthcheck]
command = ["redis-cli", "ping"]
interval = 30
timeout = 10
retries = 3
```

## Deployment Procedures

### Automated Deployment (Recommended)

**Using Deployment Script:**
```bash
# Full production deployment with safety checks
./scripts/deploy-production.sh deploy

# Check deployment status
./scripts/deploy-production.sh status

# View deployment logs
./scripts/deploy-production.sh logs
```

**Script Features:**
- Pre-deployment validation
- Automated testing
- Database migration handling
- Health check verification
- Rollback capability
- Deployment logging

### Manual Deployment

**Step 1: Prepare Repository**
```bash
# Ensure clean working directory
git status
git add .
git commit -m "Deploy: version x.x.x"
git push origin main
```

**Step 2: Link Railway Project**
```bash
railway link f672d6bf-ac6b-4d62-9a38-158919110629
```

**Step 3: Deploy Services**
```bash
# Deploy all services
railway up --detach

# Or deploy specific service
railway up --service web --detach
```

**Step 4: Verify Deployment**
```bash
# Check service status
railway status

# View logs
railway logs --service web

# Test health endpoints
curl https://your-app.railway.app/health
```

### Database Migrations

**Automatic Migration (Recommended):**
```bash
# Migrations run automatically during deployment
# via the start command in each service
```

**Manual Migration:**
```bash
# Run migrations manually if needed
railway run --service web alembic upgrade head
```

## Environment-Specific Deployments

### Development Environment

**Local Development:**
```bash
# Start all services locally
./scripts/dev-workflow.sh start

# Or start services individually
crypto-newsletter serve --dev    # Web service
crypto-newsletter worker         # Worker service
crypto-newsletter beat           # Beat service
redis-server                     # Redis service
```

**Development Database:**
```bash
# Use local PostgreSQL or SQLite
DATABASE_URL=sqlite:///dev.db

# Or use Neon development branch
DATABASE_URL=postgresql://user:pass@host/dev_db
```

### Staging Environment

**Railway Preview Deployments:**
```bash
# Create preview deployment for PR
git checkout -b feature/new-feature
git push origin feature/new-feature
# Railway automatically creates preview deployment
```

**Staging Configuration:**
```bash
RAILWAY_ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=DEBUG
```

### Production Environment

**Production Configuration:**
```bash
RAILWAY_ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ENABLE_CELERY=true
```

**Production Checklist:**
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Health checks passing
- [ ] SSL certificates valid
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Rollback plan prepared

## Monitoring and Health Checks

### Health Check Endpoints

**Basic Health Check:**
```bash
curl https://your-app.railway.app/health
```

**Detailed Health Check:**
```bash
curl https://your-app.railway.app/health/detailed
```

**Admin Status:**
```bash
curl https://your-app.railway.app/admin/status
```

### Service Monitoring

**Railway Dashboard:**
- Service status and metrics
- Resource usage graphs
- Deployment history
- Log aggregation

**Custom Monitoring:**
```bash
# Use monitoring script
./scripts/monitor.sh status
./scripts/monitor.sh health
./scripts/monitor.sh watch
```

## Rollback Procedures

### Automated Rollback

**Using Deployment Script:**
```bash
# Rollback to previous deployment
./scripts/deploy-production.sh rollback
```

### Manual Rollback

**Step 1: Identify Previous Version**
```bash
# Check deployment history
railway deployments

# Get commit hash of previous version
git log --oneline -10
```

**Step 2: Rollback Code**
```bash
# Checkout previous commit
git checkout <previous-commit-hash>

# Force push to trigger redeployment
git push origin HEAD:main --force
```

**Step 3: Verify Rollback**
```bash
# Check service status
railway status

# Run health checks
./scripts/deploy-production.sh health
```

### Database Rollback

**Migration Rollback:**
```bash
# Rollback database migrations if needed
railway run --service web alembic downgrade -1

# Or rollback to specific revision
railway run --service web alembic downgrade <revision>
```

## Troubleshooting

### Common Deployment Issues

**1. Service Won't Start**
```bash
# Check logs for errors
railway logs --service web

# Common causes:
# - Missing environment variables
# - Database connection issues
# - Port binding problems
```

**2. Database Connection Failed**
```bash
# Verify DATABASE_URL
railway variables

# Test connection
railway run --service web python -c "
from crypto_newsletter.shared.database.connection import get_db_session
import asyncio
async def test():
    async with get_db_session() as db:
        await db.execute('SELECT 1')
    print('Database connection successful')
asyncio.run(test())
"
```

**3. Redis Connection Issues**
```bash
# Check Redis service status
railway status

# Verify REDIS_URL
railway variables

# Test Redis connection
railway run --service worker python -c "
import redis
r = redis.from_url('$REDIS_URL')
r.ping()
print('Redis connection successful')
"
```

**4. Celery Tasks Not Processing**
```bash
# Check worker service logs
railway logs --service worker

# Verify beat service is running
railway logs --service beat

# Check task queue
railway run --service worker python -c "
from crypto_newsletter.core.scheduling.tasks import get_active_tasks
print(get_active_tasks())
"
```

### Performance Issues

**High Memory Usage:**
```bash
# Check service metrics in Railway dashboard
# Consider scaling up service resources
# Review memory-intensive operations
```

**Slow API Responses:**
```bash
# Check database query performance
# Review API endpoint implementations
# Consider adding caching
```

**Task Queue Backlog:**
```bash
# Scale worker service
railway scale --service worker --replicas 3

# Check task processing rates
./scripts/monitor.sh metrics
```

## Security Considerations

### Environment Variables

**Secure Storage:**
- Use Railway's environment variable management
- Never commit secrets to repository
- Rotate secrets regularly
- Use different secrets per environment

**Access Control:**
- Limit Railway project access
- Use service-specific environment variables
- Implement least privilege principle

### Network Security

**HTTPS Configuration:**
- Railway provides automatic HTTPS
- Verify SSL certificate validity
- Configure security headers

**API Security:**
- Implement rate limiting
- Validate all inputs
- Use secure authentication (future)

## Backup and Recovery

### Database Backups

**Automated Backups:**
- Neon provides automatic daily backups
- Point-in-time recovery available
- Cross-region backup replication

**Manual Backups:**
```bash
# Create manual backup
./scripts/db-manager.sh backup

# Export data
./scripts/db-manager.sh export
```

### Application Backups

**Configuration Backup:**
```bash
# Backup environment variables
railway variables --json > backup/env-vars.json

# Backup Railway configuration
cp railway.toml backup/
```

### Recovery Procedures

**Database Recovery:**
```bash
# Restore from backup
./scripts/db-manager.sh restore backup/backup_20250110_120000.sql

# Verify data integrity
./scripts/db-manager.sh stats
```

**Service Recovery:**
```bash
# Restart failed services
railway restart --service web

# Redeploy if necessary
railway up --service web
```

## Maintenance Procedures

### Regular Maintenance

**Daily:**
- Monitor service health
- Check error logs
- Verify data ingestion

**Weekly:**
- Review performance metrics
- Update dependencies
- Run security scans

**Monthly:**
- Database maintenance
- Backup verification
- Capacity planning

### Maintenance Scripts

```bash
# System cleanup
./scripts/monitor.sh cleanup

# Database maintenance
./scripts/db-manager.sh vacuum

# Performance optimization
./scripts/monitor.sh optimize
```

## Support and Escalation

### Monitoring Alerts

**Critical Alerts:**
- Service downtime
- Database connectivity issues
- High error rates

**Warning Alerts:**
- High resource usage
- Slow response times
- Task queue backlog

### Escalation Procedures

1. **Check service status** via Railway dashboard
2. **Review logs** for error patterns
3. **Run health checks** using monitoring scripts
4. **Apply fixes** based on troubleshooting guide
5. **Escalate** to development team if needed

### Contact Information

- **Railway Support**: https://railway.app/help
- **Neon Support**: https://neon.tech/docs/support
- **Development Team**: [Your team contact information]
