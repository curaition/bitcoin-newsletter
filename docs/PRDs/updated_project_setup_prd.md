# Project Setup & Development Standards (Updated)
## Product Requirements Document (PRD)

### Executive Summary
A comprehensive development foundation that establishes project structure, development workflows, deployment processes, and documentation standards for the crypto newsletter system. This PRD leverages the existing CoinDesk API integration and creates a scalable development environment that supports the implementation of the 4 core system PRDs.

---

## 1. Product Overview

### Vision
Create a robust, well-documented development environment that enables efficient implementation of the crypto newsletter system while maintaining code quality, deployment reliability, and developer productivity.

### Core Value Proposition
- **CoinDesk API Foundation**: Leverage proven CoinDesk API integration for reliable data ingestion
- **Consistent Standards**: Unified development practices across all system components
- **Railway + Neon Architecture**: Streamlined deployment with Railway + external Neon database
- **UV-Based Development**: Modern Python package management with UV throughout
- **Scalable Architecture**: Foundation that supports system growth and multi-source expansion

---

## 2. Data Source Integration

### 2.1 CoinDesk API Specification
**Primary Data Source**: CoinDesk Latest Articles API
- **Endpoint**: `https://data-api.coindesk.com/news/v1/article/list`
- **API Key**: `346bed562339e612d8c119b80e25f162386d81bdbe323f381a85eab2f0cb74fb`
- **Rate Limits**: 11,000 calls/month (free tier) = ~366 calls/day
- **Target Schedule**: Every 4 hours = 6 calls/day (well within limits)

**API Parameters**:
```python
{
    "lang": "EN",
    "limit": 50,  # Adjust based on 24hr filtering needs
    "source_ids": "coindesk,cointelegraph,bitcoinmagazine,coingape,blockworks,dailyhodl,cryptoslate,cryptopotato,decrypt,theblock,cryptobriefing,bitcoin.com,newsbtc",
    "categories": "BTC",  # Start with Bitcoin focus
    "api_key": "346bed562339e612d8c119b80e25f162386d81bdbe323f381a85eab2f0cb74fb"
}
```

### 2.2 Database Schema Alignment
**Existing Schema** (already proven and indexed):
```sql
-- Publishers table (source management)
publishers (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER UNIQUE NOT NULL,  -- Maps to CoinDesk SOURCE_ID
    source_key TEXT,                    -- Maps to CoinDesk source identifier
    name TEXT NOT NULL,                 -- Publisher display name
    image_url TEXT,                     -- Publisher logo/image
    url TEXT,                          -- Publisher website
    language TEXT DEFAULT 'EN',
    source_type TEXT DEFAULT 'API',
    launch_date TIMESTAMPTZ,
    benchmark_score INTEGER,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    last_updated_ts BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Articles table (main content storage)
articles (
    id BIGSERIAL PRIMARY KEY,
    external_id BIGINT UNIQUE NOT NULL,        -- Maps to CoinDesk ID
    guid TEXT UNIQUE NOT NULL,                 -- Maps to CoinDesk GUID
    title TEXT NOT NULL,                       -- Maps to CoinDesk TITLE
    subtitle TEXT,                             -- Maps to CoinDesk SUBTITLE
    authors TEXT,                              -- Maps to CoinDesk AUTHORS
    url TEXT UNIQUE NOT NULL,                  -- Maps to CoinDesk URL
    body TEXT,                                 -- Maps to CoinDesk BODY
    keywords TEXT,                             -- Maps to CoinDesk KEYWORDS
    language TEXT,                             -- Maps to CoinDesk LANG
    image_url TEXT,                            -- Maps to CoinDesk IMAGE_URL
    published_on TIMESTAMPTZ,                  -- Converted from CoinDesk PUBLISHED_ON (unix timestamp)
    published_on_ns BIGINT,                    -- Maps to CoinDesk PUBLISHED_ON_NS
    upvotes INTEGER DEFAULT 0,                 -- Maps to CoinDesk UPVOTES
    downvotes INTEGER DEFAULT 0,               -- Maps to CoinDesk DOWNVOTES
    score INTEGER DEFAULT 0,                   -- Maps to CoinDesk SCORE
    sentiment TEXT CHECK (sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')), -- Maps to CoinDesk SENTIMENT
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'DELETED')),
    created_on TIMESTAMPTZ,                    -- Maps to CoinDesk CREATED_ON (unix timestamp)
    updated_on TIMESTAMPTZ,                    -- Maps to CoinDesk UPDATED_ON (unix timestamp)
    publisher_id BIGINT REFERENCES publishers(id),
    source_id INTEGER,                         -- Maps to CoinDesk SOURCE_ID for direct reference
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories table (article categorization)
categories (
    id BIGSERIAL PRIMARY KEY,
    category_id INTEGER UNIQUE NOT NULL,      -- Maps to CoinDesk CATEGORY_DATA.ID
    name TEXT NOT NULL,                       -- Maps to CoinDesk CATEGORY_DATA.NAME
    category TEXT NOT NULL                    -- Maps to CoinDesk CATEGORY_DATA.CATEGORY
);

-- Article categories junction table
article_categories (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id),
    category_id BIGINT REFERENCES categories(id),
    UNIQUE(article_id, category_id)
);
```

**Schema Notes**:
- ✅ **Perfect Alignment**: Current schema maps directly to CoinDesk API response
- ✅ **Proven Indexing**: Full-text search, temporal, and relational indexes already optimized
- ✅ **Deduplication Ready**: UNIQUE constraints on `external_id`, `guid`, and `url`
- ✅ **Category Support**: Junction table handles multiple categories per article

---

## 3. Development Environment Specifications

### 3.1 Python Environment Management
**Primary Tool**: UV (Ultra-fast Python package installer and resolver)

**Project Structure**:
```
crypto-newsletter/
├── pyproject.toml              # UV project configuration
├── uv.lock                     # Lock file for reproducible builds
├── .python-version             # Python version specification (3.11+)
├── README.md                   # Project documentation
├── .env.example                # Environment variables template
├── .env.development            # Development environment variables
├── .env.production             # Production environment variables
├── .gitignore                  # Git ignore patterns
├── railway.toml                # Railway deployment configuration
├── requirements.txt            # Generated from UV for Railway compatibility
├── 
├── src/
│   ├── crypto_newsletter/
│   │   ├── __init__.py
│   │   ├── core/               # Core Data Pipeline (PRD 1)
│   │   │   ├── __init__.py
│   │   │   ├── ingestion/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── coindesk_client.py
│   │   │   │   ├── article_processor.py
│   │   │   │   └── deduplication.py
│   │   │   ├── storage/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py
│   │   │   │   └── models.py
│   │   │   └── scheduling/
│   │   │       ├── __init__.py
│   │   │       └── tasks.py
│   │   ├── analysis/           # Signal Detection & Analysis (PRD 2)
│   │   ├── newsletter/         # Newsletter Generation (PRD 3)
│   │   ├── monitoring/         # Monitoring & Prompt Engineering (PRD 4)
│   │   ├── shared/             # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── database/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection.py
│   │   │   │   └── migrations.py
│   │   │   ├── models/
│   │   │   ├── config/
│   │   │   │   ├── __init__.py
│   │   │   │   └── settings.py
│   │   │   └── utils/
│   │   └── cli/                # Command-line interface
│   │       ├── __init__.py
│   │       └── main.py
├── 
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── 
├── docs/
├── scripts/
└── alembic/                    # Database migrations
    ├── env.py
    ├── script.py.mako
    └── versions/
```

**UV Configuration (pyproject.toml)**:
```toml
[project]
name = "crypto-newsletter"
version = "0.1.0"
description = "AI-powered cryptocurrency newsletter with signal detection"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    # Core Framework
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    
    # Database
    "asyncpg>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.0",
    
    # Task Queue & Scheduling
    "celery[redis]>=5.3.0",
    "redis>=5.0.0",
    "celery-beat>=2.5.0",
    
    # HTTP Client & API Integration
    "httpx>=0.25.0",
    "aiohttp>=3.9.0",
    "requests>=2.31.0",
    
    # Data Processing
    "pandas>=2.1.0",
    
    # AI/ML (for future phases)
    "pydantic-ai>=0.0.1",
    "google-generativeai>=0.3.0",
    
    # Utilities
    "python-dotenv>=1.0.0",
    "loguru>=0.7.0",
    "typer>=0.9.0",
    "click>=8.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "pre-commit>=3.5.0",
]

[project.scripts]
crypto-newsletter = "crypto_newsletter.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

### 3.2 Development Workflow Standards

**Environment Setup Process**:
```bash
# 1. Clone repository
git clone <repository-url>
cd crypto-newsletter

# 2. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Create and activate virtual environment
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# 4. Install dependencies
uv pip install -e .[dev]

# 5. Set up pre-commit hooks
pre-commit install

# 6. Copy and configure environment variables
cp .env.example .env.development
# Edit .env.development with your configuration

# 7. Initialize database (connect to existing Neon database)
alembic upgrade head

# 8. Run tests to verify setup
pytest

# 9. Start development server
uv run crypto-newsletter serve --dev
```

**Development Commands**:
```bash
# Development server
uv run crypto-newsletter serve --dev

# Run CoinDesk ingestion manually
uv run crypto-newsletter ingest-articles

# Run tests
uv run pytest

# Code formatting
uv run black src/ tests/
uv run ruff check src/ tests/ --fix

# Type checking
uv run mypy src/

# Database migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
```

---

## 4. Railway Deployment Architecture

### 4.1 Railway Project Structure
**Project**: `bitcoin-newsletter`
**Environment Strategy**:
```
├── Production Environment (main branch)
│   ├── Web Service (FastAPI + UV)
│   ├── Worker Service (Celery Workers)
│   ├── Beat Service (Celery Scheduler)
│   └── Redis Service (Task Queue)
├── 
├── Staging Environment (staging branch)
│   ├── Web Service
│   ├── Worker Service  
│   ├── Beat Service
│   └── Redis Service
├── 
└── PR Environments (automatic)
    └── Web Service (minimal for testing)
```

**External Services**:
- **Neon Database**: Separate production and development databases
- **Shared Variables**: API keys, database URLs managed centrally

### 4.2 Railpack Configuration

**Why Railpack over Nixpacks**:
- ✅ **Native UV Support**: Railpack detects `pyproject.toml` and `uv.lock` automatically
- ✅ **Faster Builds**: BuildKit-based image construction
- ✅ **Zero Config**: Automatically detects Python projects with UV
- ✅ **Smaller Images**: More efficient than Nixpacks for Python apps
- ✅ **UV-First**: Uses `uv sync` for dependency installation

**Project Detection**: Railpack automatically identifies our project as Python due to:
- ✅ `pyproject.toml` file present
- ✅ `uv.lock` file present
- ✅ Main application structure

**Railpack Auto-Configuration**:
```python
# Railpack automatically detects these patterns:
# 1. Python version from .python-version (3.11+)
# 2. Dependencies from uv.lock (uses uv sync)
# 3. Start command from pyproject.toml scripts section
# 4. Environment variables for Python optimization
```

**Optional Railpack Customization (railpack.json)**:
```json
{
  "python": {
    "version": "3.11",
    "manager": "uv"
  },
  "build": {
    "commands": [
      "uv sync --frozen",
      "uv run alembic upgrade head"
    ]
  },
  "start": {
    "cmd": "uv run crypto-newsletter serve --production"
  },
  "environment": {
    "PYTHONFAULTHANDLER": "1",
    "PYTHONUNBUFFERED": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "UV_SYSTEM_PYTHON": "1"
  }
}
```

### 4.3 Railway Configuration (railway.toml)

**Multi-Service Configuration**:
```toml
[build]
builder = "railpack"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "always"

[env]
PORT = { default = "8000" }
RAILWAY_ENVIRONMENT = { default = "production" }

# Shared Variables (defined at project level)
DATABASE_URL = { default = "${{shared.DATABASE_URL}}" }
REDIS_URL = { default = "${{Redis.REDIS_URL}}" }
COINDESK_API_KEY = { default = "${{shared.COINDESK_API_KEY}}" }

# Service-specific configurations
[[services]]
name = "web"
source = "."

[services.web]
startCommand = "uv run crypto-newsletter serve"
tcpProxyPort = 8000
variables = { SERVICE_TYPE = "web" }

[[services]]
name = "worker"
source = "."

[services.worker]
startCommand = "uv run celery -A crypto_newsletter.shared.celery worker --loglevel=info --concurrency=2"
variables = { SERVICE_TYPE = "worker" }

[[services]]
name = "beat"
source = "."

[services.beat]
startCommand = "uv run celery -A crypto_newsletter.shared.celery beat --loglevel=info"
variables = { SERVICE_TYPE = "scheduler" }

# Environment-specific overrides
[environments.staging]
[environments.staging.services.web]
variables = { LOG_LEVEL = "DEBUG" }

[environments.production] 
[environments.production.services.web]
variables = { LOG_LEVEL = "WARNING" }

# PR Environments (lightweight)
[environments.pr]
services = ["web"]  # Only deploy web service for PRs
[environments.pr.services.web]
variables = { 
  LOG_LEVEL = "DEBUG",
  DISABLE_CELERY = "true",
  DATABASE_URL = "${{shared.DEV_DATABASE_URL}}"
}
```

### 4.4 Environment Management Strategy

**Shared Variables Configuration**:
```bash
# Set at Railway project level (shared across all environments)
railway variables set --shared \
  COINDESK_API_KEY="346bed562339e612d8c119b80e25f162386d81bdbe323f381a85eab2f0cb74fb" \
  GEMINI_API_KEY="your_gemini_key" \
  PROD_DATABASE_URL="postgresql://user:pass@neon-prod/crypto_newsletter" \
  DEV_DATABASE_URL="postgresql://user:pass@neon-dev/crypto_newsletter"

# Environment-specific variables
railway variables set --environment production \
  DATABASE_URL="${{shared.PROD_DATABASE_URL}}" \
  LOG_LEVEL="WARNING"

railway variables set --environment staging \
  DATABASE_URL="${{shared.DEV_DATABASE_URL}}" \
  LOG_LEVEL="DEBUG"
```

**Private Network Configuration**:
```python
# Use Railway's private network for inter-service communication
# Redis URL automatically uses private networking
REDIS_URL = "${{Redis.RAILWAY_PRIVATE_DOMAIN}}:6379"

# Database connection uses external Neon (secure connection)
DATABASE_URL = "postgresql://user:pass@ep-name.region.neon.tech/dbname"
```

### 4.5 Webhook Integration

**Deployment Webhooks**:
```toml
# In Railway project settings
[webhooks]
deploy = [
  "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",  # Deployment notifications
  "https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"  # Status updates
]
```

**Custom Application Webhooks**:
```python
# src/crypto_newsletter/shared/webhooks.py
from fastapi import APIRouter, Request
import hmac
import hashlib

webhook_router = APIRouter(prefix="/webhooks")

@webhook_router.post("/railway/deploy")
async def railway_deploy_webhook(request: Request):
    """Handle Railway deployment notifications"""
    payload = await request.body()
    
    # Verify webhook signature if configured
    signature = request.headers.get("x-railway-signature")
    if signature:
        verify_webhook_signature(payload, signature)
    
    deployment_data = await request.json()
    
    # Process deployment notification
    await handle_deployment_notification(deployment_data)
    
    return {"status": "received"}

@webhook_router.post("/github/pr")
async def github_pr_webhook(request: Request):
    """Handle GitHub PR events for custom logic"""
    payload = await request.json()
    
    if payload["action"] in ["opened", "synchronize"]:
        # Trigger custom PR environment setup
        await setup_pr_environment(payload["pull_request"])
    
    return {"status": "processed"}
```

### 4.6 Environment-Specific Deployment Strategy

**Branch-Based Deployment**:
```yaml
# .github/workflows/railway-deploy.yml
name: Railway Deployment

on:
  push:
    branches: [main, staging]
  pull_request:
    types: [opened, synchronize]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install Railway CLI
      run: npm install -g @railway/cli
      
    - name: Deploy to Railway
      run: |
        if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
          railway up --environment production
        elif [[ "${{ github.ref }}" == "refs/heads/staging" ]]; then
          railway up --environment staging
        else
          # PR environments handled automatically by Railway
          echo "PR environment will be created automatically"
        fi
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

**Environment Sync Strategy**:
```bash
# Sync services from staging to production
railway service sync --from staging --to production --service web
railway service sync --from staging --to production --service worker
railway service sync --from staging --to production --service beat

# Sync variables (careful with environment-specific values)
railway variables copy --from staging --to production --exclude DATABASE_URL,LOG_LEVEL
```

### 4.7 Railpack CLI Integration

**Local Development with Railpack**:
```bash
# Install Railpack CLI
npm install -g @railpack/cli

# Test build locally (mimics Railway build process)
railpack build

# Test with specific configuration
railpack build --config railpack.json

# Debug build process
railpack build --verbose

# Generate Dockerfile for inspection
railpack dockerfile > Dockerfile.railpack
```

**UV + Railpack Optimization**:
```json
// railpack.json - optimized for UV
{
  "python": {
    "version": "3.11",
    "manager": "uv"
  },
  "cache": {
    "paths": [
      ".venv",
      "uv.lock"
    ]
  },
  "build": {
    "commands": [
      "uv sync --frozen --no-dev",
      "uv pip compile --generate-hashes requirements.in > requirements.txt"
    ]
  },
  "optimization": {
    "removeDevDependencies": true,
    "compressLayers": true
  }
}
```

### 4.8 Production Readiness & Monitoring

**Health Check Implementation**:
```python
# src/crypto_newsletter/shared/health.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from crypto_newsletter.shared.database import get_db_session
import redis
import os

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """Comprehensive health check for Railway"""
    checks = {
        "status": "healthy",
        "service": os.getenv("SERVICE_TYPE", "web"),
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "checks": {}
    }
    
    # Database connectivity
    try:
        async with get_db_session() as db:
            await db.execute(text("SELECT 1"))
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["checks"]["database"] = f"unhealthy: {e}"
        checks["status"] = "unhealthy"
    
    # Redis connectivity (for worker services)
    if os.getenv("SERVICE_TYPE") in ["worker", "scheduler"]:
        try:
            redis_client = redis.from_url(os.getenv("REDIS_URL"))
            redis_client.ping()
            checks["checks"]["redis"] = "healthy"
        except Exception as e:
            checks["checks"]["redis"] = f"unhealthy: {e}"
            checks["status"] = "unhealthy"
    
    # CoinDesk API reachability (for main service)
    if os.getenv("SERVICE_TYPE") == "web":
        try:
            # Quick API key validation
            api_key = os.getenv("COINDESK_API_KEY")
            if not api_key or len(api_key) < 32:
                raise ValueError("Invalid API key")
            checks["checks"]["coindesk_api"] = "configured"
        except Exception as e:
            checks["checks"]["coindesk_api"] = f"issue: {e}"
    
    if checks["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=checks)
    
    return checks

@health_router.get("/ready")
async def readiness_check():
    """Simple readiness probe"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
```

**Webhook Configuration for Notifications**:
```python
# Railway Project Settings → Webhooks
{
  "deployment_webhooks": [
    {
      "url": "https://hooks.slack.com/services/YOUR/TEAM/WEBHOOK",
      "events": ["deployment.started", "deployment.completed", "deployment.failed"],
      "environments": ["production", "staging"]
    }
  ],
  "alert_webhooks": [
    {
      "url": "https://discord.com/api/webhooks/YOUR/WEBHOOK",
      "events": ["service.crash", "service.restart", "health_check.failed"],
      "environments": ["production"]
    }
  ]
}
```

**Custom Monitoring Integration**:
```python
# src/crypto_newsletter/shared/monitoring.py
import httpx
from datetime import datetime
import os

class RailwayIntegration:
    def __init__(self):
        self.project_id = os.getenv("RAILWAY_PROJECT_ID")
        self.environment = os.getenv("RAILWAY_ENVIRONMENT", "development")
        self.service_name = os.getenv("SERVICE_TYPE", "web")
    
    async def report_ingestion_metrics(self, articles_processed: int, errors: int):
        """Report custom metrics to external monitoring"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "service": self.service_name,
            "metrics": {
                "articles_processed": articles_processed,
                "errors": errors,
                "success_rate": (articles_processed / (articles_processed + errors)) if articles_processed + errors > 0 else 1.0
            }
        }
        
        # Send to custom monitoring endpoint
        webhook_url = os.getenv("MONITORING_WEBHOOK_URL")
        if webhook_url:
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=metrics)
    
    async def report_deployment_success(self):
        """Custom deployment success notification"""
        deployment_info = {
            "project": "bitcoin-newsletter",
            "environment": self.environment,
            "service": self.service_name,
            "status": "deployed",
            "timestamp": datetime.utcnow().isoformat(),
            "health_check": f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')}/health"
        }
        
        # Custom notification logic
        await self._send_deployment_notification(deployment_info)
```

### 4.9 Development vs Production Parity

**Local Development Configuration**:
```bash
# .env.development
RAILWAY_ENVIRONMENT=development
SERVICE_TYPE=web
DATABASE_URL=postgresql://localhost/crypto_newsletter_dev
REDIS_URL=redis://localhost:6379
COINDESK_API_KEY=346bed562339e612d8c119b80e25f162386d81bdbe323f381a85eab2f0cb74fb
LOG_LEVEL=DEBUG
ENABLE_CELERY=false  # Disable for local development
```

**Production Configuration**:
```bash
# Railway Environment Variables (automatically set)
RAILWAY_ENVIRONMENT=production
RAILWAY_PROJECT_ID=abc123
RAILWAY_SERVICE_ID=xyz789
RAILWAY_DEPLOYMENT_ID=deploy123
RAILWAY_PUBLIC_DOMAIN=bitcoin-newsletter-production.up.railway.app
RAILWAY_PRIVATE_DOMAIN=bitcoin-newsletter-production.railway.internal
SERVICE_TYPE=web  # or worker, scheduler
DATABASE_URL=${{shared.PROD_DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
COINDESK_API_KEY=${{shared.COINDESK_API_KEY}}
LOG_LEVEL=WARNING
```

**Development Parity Script**:
```bash
#!/bin/bash
# scripts/setup-dev-parity.sh

echo "Setting up development environment with production parity..."

# Start local services that match Railway
docker run -d --name crypto-newsletter-redis -p 6379:6379 redis:7-alpine
docker run -d --name crypto-newsletter-postgres -p 5432:5432 \
  -e POSTGRES_DB=crypto_newsletter_dev \
  -e POSTGRES_USER=dev \
  -e POSTGRES_PASSWORD=dev123 \
  postgres:15-alpine

# Wait for services to start
sleep 5

# Set up UV environment
uv venv
source .venv/bin/activate
uv pip install -e .[dev]

# Set up database
export DATABASE_URL="postgresql://dev:dev123@localhost/crypto_newsletter_dev"
uv run alembic upgrade head

# Test local setup
uv run crypto-newsletter --help
uv run pytest tests/health/

echo "Development environment ready! 🚀"
echo "Start the app with: uv run crypto-newsletter serve --dev"
```

---

## 5. Core Data Pipeline Implementation

### 5.1 CoinDesk API Client
```python
# src/crypto_newsletter/core/ingestion/coindesk_client.py
import httpx
from typing import List, Dict, Any
from datetime import datetime, timezone
from crypto_newsletter.shared.config import get_settings

class CoinDeskAPIClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.coindesk_base_url
        self.api_key = self.settings.coindesk_api_key
        
    async def get_latest_articles(
        self, 
        limit: int = 50,
        language: str = "EN",
        categories: List[str] = None
    ) -> Dict[str, Any]:
        """Fetch latest articles from CoinDesk API"""
        
        if categories is None:
            categories = ["BTC"]
            
        params = {
            "lang": language,
            "limit": limit,
            "categories": ",".join(categories),
            "api_key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/news/v1/article/list",
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    def filter_recent_articles(
        self, 
        api_response: Dict[str, Any], 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Filter articles to only include those from last N hours"""
        
        cutoff_timestamp = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent_articles = []
        
        for article in api_response.get("Data", []):
            if article.get("PUBLISHED_ON", 0) > cutoff_timestamp:
                recent_articles.append(article)
                
        return recent_articles
```

### 5.2 Article Processing
```python
# src/crypto_newsletter/core/ingestion/article_processor.py
from sqlalchemy.ext.asyncio import AsyncSession
from crypto_newsletter.shared.models import Article, Publisher, Category
from typing import Dict, List, Any

class ArticleProcessor:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
    async def process_articles(self, articles: List[Dict[str, Any]]) -> int:
        """Process articles from CoinDesk API response"""
        processed_count = 0
        
        for article_data in articles:
            try:
                # Check if article already exists
                if await self._article_exists(article_data):
                    continue
                    
                # Process publisher
                publisher = await self._process_publisher(article_data.get("SOURCE_DATA", {}))
                
                # Create article
                article = await self._create_article(article_data, publisher.id)
                
                # Process categories
                await self._process_categories(article, article_data.get("CATEGORY_DATA", []))
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing article {article_data.get('ID')}: {e}")
                continue
                
        await self.db.commit()
        return processed_count
    
    async def _article_exists(self, article_data: Dict[str, Any]) -> bool:
        """Check if article already exists using deduplication logic"""
        external_id = article_data.get("ID")
        guid = article_data.get("GUID")
        url = article_data.get("URL")
        
        # Check multiple deduplication criteria
        result = await self.db.execute(
            text("""
                SELECT 1 FROM articles 
                WHERE external_id = :external_id 
                   OR guid = :guid 
                   OR url = :url
                LIMIT 1
            """),
            {"external_id": external_id, "guid": guid, "url": url}
        )
        
        return result.first() is not None
```

### 5.3 Scheduling & Task Management
```python
# src/crypto_newsletter/core/scheduling/tasks.py
from celery import Celery
from celery.schedules import crontab
from crypto_newsletter.core.ingestion import CoinDeskAPIClient, ArticleProcessor

# Celery configuration
celery_app = Celery('crypto_newsletter')
celery_app.conf.update(
    broker_url=get_settings().redis_url,
    result_backend=get_settings().redis_url,
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'ingest-coindesk-articles': {
            'task': 'crypto_newsletter.core.scheduling.tasks.ingest_articles',
            'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        },
    },
)

@celery_app.task(bind=True, max_retries=3)
async def ingest_articles(self):
    """Scheduled task to ingest articles from CoinDesk API"""
    try:
        client = CoinDeskAPIClient()
        processor = ArticleProcessor(get_db_session())
        
        # Fetch latest articles
        api_response = await client.get_latest_articles()
        
        # Filter to last 24 hours
        recent_articles = client.filter_recent_articles(
            api_response, 
            hours=get_settings().article_retention_hours
        )
        
        # Process articles
        processed_count = await processor.process_articles(recent_articles)
        
        logger.info(f"Processed {processed_count} new articles")
        return {"processed_count": processed_count}
        
    except Exception as exc:
        logger.error(f"Article ingestion failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # 5 minute retry delay
```

---

## 6. Enhanced Implementation Roadmap

### Week 1: Foundation Setup (Core Infrastructure)
**Goals**: Establish development environment and basic data ingestion
- Set up UV-based Python environment with all dependencies
- Configure Railway deployment with Railpack (not Nixpack)
- Establish GitHub → Railway deployment pipeline
- Create Neon database connection and verify schema alignment
- Implement basic CoinDesk API client with authentication

**Deliverables**:
- ✅ Working UV development environment
- ✅ Railway staging environment deployment
- ✅ CoinDesk API integration returning data
- ✅ Database connection verified
- ✅ Basic CLI tool for manual article ingestion

**Testing Criteria**:
- Manual article ingestion works via CLI
- Railway deployment successful
- Database writes successful
- Zero API rate limit issues

### Week 2: Data Pipeline Implementation (Automated Ingestion)
**Goals**: Replace n8n workflow with Python-based automated ingestion
- Implement complete CoinDesk API article processing
- Create deduplication logic using existing database constraints
- Set up Celery + Redis for 4-hour scheduling
- Implement error handling and retry logic
- Add basic logging and monitoring

**Deliverables**:
- ✅ Automated 4-hour article ingestion schedule
- ✅ Complete article processing pipeline
- ✅ Deduplication preventing duplicate storage
- ✅ Publisher and category data processing
- ✅ Error handling with exponential backoff

**Testing Criteria**:
- Scheduled ingestion runs successfully every 4 hours
- Zero duplicate articles in database
- All CoinDesk response fields properly mapped
- Error recovery working for API failures

### Week 3: MVP Newsletter Integration (Preserve Working Solution)
**Goals**: Integrate existing newsletter generation while building new analysis layer
- Extract newsletter generation logic from n8n PoC
- Create newsletter service using existing HTML template
- Implement basic article selection (most recent 10 articles)
- Set up email delivery system
- Prepare foundation for AI analysis integration

**Deliverables**:
- ✅ Newsletter generation service
- ✅ HTML email template preserved from PoC
- ✅ Article selection algorithm
- ✅ Email delivery integration
- ✅ Manual newsletter generation via CLI

**Testing Criteria**:
- Generated newsletters match PoC quality
- Email delivery successful
- Article selection working
- HTML template rendering correctly

### Week 4: Production Deployment & Monitoring (Operational Excellence)
**Goals**: Production-ready deployment with monitoring and controls
- Set up production Railway environment
- Implement comprehensive logging with structured output
- Add health checks and monitoring endpoints
- Create manual override capabilities
- Establish backup and recovery procedures

**Deliverables**:
- ✅ Production Railway environment
- ✅ Staging → Production promotion process
- ✅ Health monitoring endpoints
- ✅ Manual controls for emergency operations
- ✅ Documentation and runbooks

**Testing Criteria**:
- Production deployment stable
- Monitoring shows healthy system operation
- Manual overrides working
- Zero data loss during operations

---

## 7. Risk Mitigation Strategies

### Technical Risks
- **Railway CORS/Port Issues**: Use Railway's TCP proxy and proper health check endpoints
- **CoinDesk API Rate Limits**: Conservative 6 calls/day vs 366 limit provides 60x safety margin
- **Database Connection Issues**: Connection pooling and retry logic with exponential backoff
- **UV Deployment Compatibility**: Generate requirements.txt for Railway Railpack compatibility

### Operational Risks
- **Data Loss**: Database foreign key constraints and transaction safety
- **Service Disruption**: Staging environment for testing before production deployment
- **API Changes**: Comprehensive error handling and graceful degradation
- **Cost Overruns**: Conservative resource allocation and monitoring

### Development Risks
- **Local Development Issues**: UV environment isolation and clear setup documentation
- **GitHub Integration Problems**: Separate staging branch for testing deployments
- **Schema Migration Issues**: Alembic migrations with rollback capability

---

## 8. Success Metrics

### Development Productivity
- **Setup Time**: New developers productive within 2 hours using UV
- **Deployment Success**: >95% successful deployments to Railway
- **Code Quality**: >90% test coverage maintained
- **Documentation Currency**: <48 hour lag between code and documentation updates

### System Reliability
- **Ingestion Success**: >98% successful 4-hour ingestion cycles
- **Data Integrity**: 100% - zero duplicate articles, zero data corruption
- **API Efficiency**: <2% of CoinDesk API rate limit used
- **Uptime**: >99% system availability

### Newsletter Quality
- **Generation Success**: 100% successful newsletter generation when triggered
- **Content Quality**: Maintain PoC-level newsletter quality during transition
- **Email Delivery**: >98% successful email delivery rate

---

## 9. Future Expansion Foundation

### Multi-Source Readiness
- **RSS Feed Framework**: Extensible design for adding new sources beyond CoinDesk
- **Source Abstraction**: Common interface for different API formats
- **Category Management**: Flexible categorization system for diverse content types

### AI Analysis Integration Points
- **Data Structure**: Article data properly structured for AI agent consumption
- **Analysis Storage**: Schema ready for analysis results and signal detection
- **Processing Pipeline**: Modular design for inserting AI analysis steps

### Scale Preparation
- **Database Optimization**: Proper indexing for future high-volume operations
- **Task Queue Scalability**: Celery configuration ready for multiple workers
- **Monitoring Hooks**: Built-in observability for performance tracking

---

*Document Version: 2.0*
*Last Updated: August 10, 2025*
*Status: Ready for Implementation*
*Updated Based On: CoinDesk API integration, Railway+Neon architecture, UV development workflow*