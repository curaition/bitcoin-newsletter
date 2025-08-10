# FastAPI Web Service Documentation

## Overview

The Crypto Newsletter FastAPI web service provides a comprehensive API for managing the Bitcoin newsletter data pipeline. It includes health monitoring, administrative functions, and public data access endpoints.

## Service Architecture

### Core Components
- **FastAPI Application**: Main web service with async support
- **Health Monitoring**: Multiple health check endpoints for Railway deployment
- **Admin API**: Task management and system administration
- **Public API**: Data access for external integrations
- **CLI Integration**: Server management through command line

### Deployment
- **Development**: Auto-reload with debug features
- **Production**: Multi-worker deployment with optimizations
- **Railway**: Health checks and environment detection
- **Docker**: Containerized deployment ready

## API Endpoints

### Health Endpoints (`/health/`)

#### `GET /health/`
Basic health check for load balancers and Railway.
```json
{
  "status": "healthy",
  "service": "crypto-newsletter",
  "timestamp": "2025-08-10T19:30:00.000Z"
}
```

#### `GET /health/ready`
Kubernetes-style readiness probe with database connectivity check.
```json
{
  "status": "ready",
  "service": "crypto-newsletter", 
  "timestamp": "2025-08-10T19:30:00.000Z"
}
```

#### `GET /health/live`
Kubernetes-style liveness probe for container orchestration.
```json
{
  "status": "alive",
  "service": "crypto-newsletter",
  "timestamp": "2025-08-10T19:30:00.000Z",
  "uptime": "running"
}
```

#### `GET /health/detailed`
Comprehensive health check with all system components.
```json
{
  "status": "healthy",
  "service": "crypto-newsletter",
  "environment": "production",
  "checks": {
    "coindesk_api": {"status": "healthy", "message": "API connection successful"},
    "database": {"status": "healthy", "message": "Database connection successful"},
    "celery_workers": {"status": "healthy", "active_workers": 2}
  },
  "timestamp": "2025-08-10T19:30:00.000Z"
}
```

#### `GET /health/metrics`
System metrics and statistics for monitoring.
```json
{
  "timestamp": "2025-08-10T19:30:00.000Z",
  "service": "crypto-newsletter",
  "database": {
    "total_articles": 1250,
    "recent_articles": 45,
    "total_publishers": 12,
    "total_categories": 8
  },
  "system": {
    "environment": "production",
    "celery_enabled": true
  }
}
```

### Public API Endpoints (`/api/`)

#### `GET /api/articles`
Get list of articles with optional filtering.

**Query Parameters:**
- `limit` (int, max 100): Maximum articles to return (default: 10)
- `offset` (int): Pagination offset (default: 0)
- `publisher_id` (int): Filter by publisher ID
- `hours_back` (int): Filter by hours back from now

**Response:**
```json
[
  {
    "id": 123,
    "external_id": 49870131,
    "title": "Bitcoin Reaches New Heights",
    "subtitle": "Market analysis and trends",
    "url": "https://example.com/article",
    "published_on": "2025-08-10T19:30:00.000Z",
    "publisher_id": 5,
    "language": "EN",
    "status": "ACTIVE"
  }
]
```

#### `GET /api/articles/{article_id}`
Get detailed information about a specific article.

**Response:**
```json
{
  "id": 123,
  "external_id": 49870131,
  "guid": "https://example.com/?p=123",
  "title": "Bitcoin Reaches New Heights",
  "subtitle": "Market analysis and trends",
  "authors": ["John Doe"],
  "url": "https://example.com/article",
  "body": "Full article content...",
  "keywords": ["bitcoin", "cryptocurrency"],
  "language": "EN",
  "image_url": "https://example.com/image.jpg",
  "published_on": "2025-08-10T19:30:00.000Z",
  "publisher_id": 5,
  "source_id": 1,
  "status": "ACTIVE",
  "created_at": "2025-08-10T19:30:00.000Z",
  "updated_at": "2025-08-10T19:30:00.000Z"
}
```

#### `GET /api/publishers`
Get list of all publishers.

**Response:**
```json
[
  {
    "id": 1,
    "source_id": 101,
    "name": "CoinDesk",
    "source_key": "coindesk",
    "url": "https://coindesk.com",
    "lang": "EN",
    "status": "ACTIVE"
  }
]
```

#### `GET /api/stats`
Get system statistics.

**Response:**
```json
{
  "total_articles": 1250,
  "recent_articles": 45,
  "total_publishers": 12,
  "total_categories": 8,
  "top_publishers": [
    {"name": "CoinDesk", "article_count": 450}
  ],
  "top_categories": [
    {"name": "Bitcoin", "article_count": 800}
  ]
}
```

#### `POST /api/webhook/trigger-ingest`
Webhook endpoint to trigger article ingestion.

**Request Body:**
```json
{
  "limit": 50,
  "hours_back": 4,
  "categories": ["BTC", "ETH"]
}
```

**Response:**
```json
{
  "success": true,
  "mode": "asynchronous",
  "task_id": "abc-123-def",
  "status": "PENDING",
  "timestamp": "2025-08-10T19:30:00.000Z"
}
```

### Admin Endpoints (`/admin/`)

#### `GET /admin/status`
Get comprehensive system status for admin dashboard.

**Response:**
```json
{
  "timestamp": "2025-08-10T19:30:00.000Z",
  "service": "crypto-newsletter",
  "environment": "production",
  "database": {
    "total_articles": 1250,
    "recent_articles_24h": 45,
    "top_publishers": [...],
    "top_categories": [...]
  },
  "celery": {
    "enabled": true,
    "workers": {"status": "healthy", "active_workers": 2},
    "active_tasks": {...}
  }
}
```

#### `POST /admin/tasks/schedule-ingest`
Schedule an immediate article ingestion task.

**Request Body:**
```json
{
  "limit": 100,
  "hours_back": 4,
  "categories": ["BTC"]
}
```

#### `GET /admin/tasks/{task_id}/status`
Get status of a specific task.

**Response:**
```json
{
  "task_id": "abc-123-def",
  "status": "SUCCESS",
  "result": {...},
  "date_done": "2025-08-10T19:30:00.000Z",
  "traceback": null
}
```

#### `GET /admin/tasks/active`
Get information about currently active tasks.

#### `POST /admin/ingest`
Trigger manual article ingestion (synchronous).

#### `GET /admin/stats`
Get comprehensive system statistics.

## Authentication

### API Key (Optional)
- Header: `X-API-Key: your-api-key`
- Development: API key not required
- Production: API key optional for public endpoints

### Security Features
- CORS configuration for cross-origin requests
- Global exception handling
- Request/response logging
- Input validation with Pydantic models

## CLI Commands

### Start Development Server
```bash
python -m crypto_newsletter.cli.main serve --dev --port 8000
```

### Start Production Server
```bash
python -m crypto_newsletter.cli.main serve --production --port 8000 --workers 4
```

## Docker Deployment

### Build Image
```bash
docker build -f docker/web.Dockerfile -t crypto-newsletter-web .
```

### Run Container
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e REDIS_URL="redis://..." \
  crypto-newsletter-web
```

## Monitoring

### Health Checks
- **Basic**: `/health/` - Simple status for load balancers
- **Readiness**: `/health/ready` - Database connectivity check
- **Liveness**: `/health/live` - Service availability check
- **Detailed**: `/health/detailed` - Comprehensive system health
- **Metrics**: `/health/metrics` - System metrics and statistics

### Logging
- Structured logging with Loguru
- Request/response logging middleware
- Error tracking and debugging
- Performance metrics

### Railway Integration
- Automatic environment detection
- Health check endpoints for Railway monitoring
- Production-optimized configuration
- Multi-service deployment support

## Development

### API Documentation
- **Swagger UI**: `/docs` (development only)
- **ReDoc**: `/redoc` (development only)
- **OpenAPI Schema**: `/openapi.json`

### Testing
```bash
# Run FastAPI integration tests
python -m pytest tests/integration/test_fastapi_service.py -v

# Test specific endpoints
python -c "from fastapi.testclient import TestClient; from crypto_newsletter.web.main import app; client = TestClient(app); print(client.get('/health/').json())"
```

### Configuration
- Environment-based configuration
- Development vs production modes
- Celery integration (optional)
- Database connection management
