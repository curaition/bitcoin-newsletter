# System Architecture

This document provides a detailed overview of the Bitcoin Newsletter system architecture, including service design, data flow, and infrastructure components.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Render Platform                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ Web Service │  │   Worker    │  │    Beat     │  │  Redis  │ │
│  │  (FastAPI)  │  │  (Celery)   │  │  (Celery)   │  │ Service │ │
│  │             │  │             │  │             │  │         │ │
│  │ Port: 8000  │  │ Background  │  │ Scheduler   │  │ Port:   │ │
│  │ HTTP/REST   │  │ Processing  │  │ Periodic    │  │ 6379    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Neon PostgreSQL                           │
│                    (Serverless Database)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External APIs                             │
│                    (CoinDesk API)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Service Architecture

### Web Service (FastAPI)

**Responsibilities:**
- REST API endpoints for article retrieval
- Health check endpoints
- Admin status interface
- Request validation and response formatting
- Rate limiting and security

**Key Components:**
```python
src/crypto_newsletter/web/
├── main.py              # FastAPI application factory
├── routers/
│   ├── articles.py      # Article endpoints
│   ├── health.py        # Health check endpoints
│   └── admin.py         # Admin endpoints
├── middleware/
│   ├── cors.py          # CORS configuration
│   ├── rate_limit.py    # Rate limiting
│   └── logging.py       # Request logging
└── dependencies/
    ├── database.py      # Database session dependency
    └── auth.py          # Authentication (future)
```

**Scaling Strategy:**
- Horizontal scaling via Render
- Stateless design for easy replication
- Database connection pooling
- Redis-based caching

### Worker Service (Celery)

**Responsibilities:**
- Background article processing
- Data ingestion from external APIs
- Article deduplication and validation
- Publisher and category management
- Error handling and retry logic

**Key Components:**
```python
src/crypto_newsletter/core/
├── ingestion/
│   ├── pipeline.py      # Main ingestion pipeline
│   ├── coindesk_client.py # API client
│   ├── article_processor.py # Article processing
│   └── deduplication.py # Duplicate detection
├── scheduling/
│   └── tasks.py         # Celery task definitions
└── storage/
    └── repository.py    # Database operations
```

**Task Types:**
- **Ingestion Tasks**: Fetch and process articles
- **Maintenance Tasks**: Database cleanup, optimization
- **Monitoring Tasks**: Health checks, metrics collection

### Beat Service (Celery Beat)

**Responsibilities:**
- Periodic task scheduling
- Cron-like job management
- Task queue management
- Schedule persistence

**Schedule Configuration:**
```python
CELERY_BEAT_SCHEDULE = {
    'ingest-articles-every-4-hours': {
        'task': 'crypto_newsletter.core.scheduling.tasks.ingest_articles',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
        'kwargs': {'limit': 50, 'hours_back': 24}
    },
    'cleanup-old-articles-daily': {
        'task': 'crypto_newsletter.core.scheduling.tasks.cleanup_old_articles',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'kwargs': {'days_old': 30}
    }
}
```

### Redis Service

**Responsibilities:**
- Celery message broker
- Task result backend
- Application caching
- Session storage (future)

**Usage Patterns:**
- **Task Queue**: Celery task distribution
- **Result Storage**: Task result caching
- **Application Cache**: Frequently accessed data
- **Rate Limiting**: Request rate tracking

## Data Architecture

### Database Schema

```sql
-- Core Tables
CREATE TABLE publishers (
    id SERIAL PRIMARY KEY,
    external_id INTEGER UNIQUE,
    name VARCHAR(255) NOT NULL,
    key VARCHAR(100) UNIQUE,
    url TEXT,
    language VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    external_id INTEGER UNIQUE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE articles (
    id BIGSERIAL PRIMARY KEY,
    external_id BIGINT UNIQUE NOT NULL,
    guid VARCHAR(255) UNIQUE,
    title TEXT NOT NULL,
    subtitle TEXT,
    url TEXT UNIQUE NOT NULL,
    body TEXT,
    published_on TIMESTAMP,
    authors TEXT,
    keywords TEXT,
    language VARCHAR(10),
    image_url TEXT,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    sentiment VARCHAR(50),
    publisher_id INTEGER REFERENCES publishers(id),
    source_id INTEGER,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE article_categories (
    id SERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(article_id, category_id)
);
```

### Indexing Strategy

**Performance Indexes:**
```sql
-- Primary access patterns
CREATE INDEX idx_articles_published_on ON articles(published_on DESC);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_publisher_id ON articles(publisher_id);

-- Search indexes
CREATE INDEX idx_articles_title_gin ON articles USING gin(to_tsvector('english', title));
CREATE INDEX idx_articles_body_gin ON articles USING gin(to_tsvector('english', body));

-- Unique constraints for deduplication
CREATE UNIQUE INDEX idx_articles_external_id ON articles(external_id);
CREATE UNIQUE INDEX idx_articles_url ON articles(url);
CREATE UNIQUE INDEX idx_articles_guid ON articles(guid) WHERE guid IS NOT NULL;
```

### Data Flow

```
External API → Ingestion Pipeline → Processing → Database Storage
     │              │                   │              │
     ▼              ▼                   ▼              ▼
CoinDesk API → Article Fetching → Deduplication → PostgreSQL
     │              │                   │              │
     │              ▼                   ▼              │
     │         Validation         Publisher Mgmt      │
     │              │                   │              │
     │              ▼                   ▼              │
     │         Transformation     Category Tagging    │
     │              │                   │              │
     └──────────────┴───────────────────┴──────────────┘
```

## Integration Architecture

### External API Integration

**CoinDesk API Client:**
```python
class CoinDeskAPIClient:
    def __init__(self):
        self.base_url = settings.coindesk_base_url
        self.api_key = settings.coindesk_api_key
        self.session = httpx.AsyncClient()
        
    async def fetch_articles(self, limit: int = 50) -> Dict[str, Any]:
        # Rate limiting, error handling, retry logic
        # Response validation and transformation
```

**Integration Patterns:**
- **Circuit Breaker**: Prevent cascade failures
- **Retry Logic**: Exponential backoff for transient failures
- **Rate Limiting**: Respect API limits
- **Caching**: Reduce API calls

### Message Queue Integration

**Celery Configuration:**
```python
# Broker and backend configuration
CELERY_BROKER_URL = settings.redis_url
CELERY_RESULT_BACKEND = settings.redis_url

# Task routing
CELERY_TASK_ROUTES = {
    'crypto_newsletter.core.scheduling.tasks.ingest_articles': {'queue': 'ingestion'},
    'crypto_newsletter.core.scheduling.tasks.cleanup_old_articles': {'queue': 'maintenance'},
}

# Serialization and compression
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_COMPRESSION = 'gzip'
```

## Deployment Architecture

### Render Platform

**Service Configuration:**
```yaml
# render.yaml
services:
  - type: web
    name: bitcoin-newsletter-api
    env: python
    buildCommand: "pip install -e ."
    startCommand: "crypto-newsletter serve --host 0.0.0.0 --port $PORT"
    healthCheckPath: "/health"

[[services]]
name = "web"
source = "."
variables = { SERVICE_TYPE = "web" }

[[services]]
name = "worker"
source = "."
variables = { SERVICE_TYPE = "worker" }

[[services]]
name = "beat"
source = "."
variables = { SERVICE_TYPE = "beat" }

[[services]]
name = "redis"
image = "redis:7-alpine"
```

**Environment Management:**
- **Development**: Local development with hot reload
- **Preview**: Render preview deployments for PRs
- **Production**: Multi-service production deployment

### Infrastructure Components

**Neon PostgreSQL:**
- Serverless PostgreSQL with auto-scaling
- Connection pooling and optimization
- Automated backups and point-in-time recovery
- Branch-based development workflows

**Render Redis:**
- Managed Redis instance
- High availability and persistence
- Memory optimization and eviction policies
- Monitoring and alerting

## Security Architecture

### Application Security

**Input Validation:**
```python
# Pydantic models for request validation
class ArticleQuery(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    hours: Optional[int] = Field(None, ge=1, le=8760)
    category: Optional[str] = Field(None, regex=r'^[A-Z_]+$')
```

**Rate Limiting:**
```python
# Slowapi integration for rate limiting
@limiter.limit("100/minute")
async def get_articles(request: Request, query: ArticleQuery):
    # Endpoint implementation
```

**Database Security:**
- Parameterized queries to prevent SQL injection
- Connection encryption (TLS)
- Credential management via environment variables
- Database user permissions and access control

### Network Security

**HTTPS Enforcement:**
- TLS termination at Render edge
- Secure headers (HSTS, CSP, etc.)
- CORS configuration for cross-origin requests

**API Security:**
- Request validation and sanitization
- Error message sanitization
- Logging and monitoring of security events

## Monitoring Architecture

### Health Checks

**Multi-level Health Checks:**
```python
async def health_check():
    checks = {
        'database': await check_database_health(),
        'redis': await check_redis_health(),
        'external_apis': await check_external_apis(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    return aggregate_health_status(checks)
```

### Metrics Collection

**Application Metrics:**
- Request/response times
- Error rates and types
- Task processing metrics
- Database query performance

**System Metrics:**
- CPU and memory usage
- Disk I/O and space
- Network throughput
- Service availability

### Logging Strategy

**Structured Logging:**
```python
# Loguru configuration
logger.configure(
    handlers=[
        {
            "sink": sys.stdout,
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            "level": "INFO"
        }
    ]
)
```

**Log Aggregation:**
- Centralized logging via Render
- Log retention and rotation
- Error tracking and alerting
- Performance monitoring

## Scalability Considerations

### Horizontal Scaling

**Service Scaling:**
- Web service: Scale based on HTTP traffic
- Worker service: Scale based on queue depth
- Beat service: Single instance (leader election)
- Redis: Managed scaling by Render

**Database Scaling:**
- Neon auto-scaling based on demand
- Connection pooling optimization
- Read replicas for read-heavy workloads
- Query optimization and indexing

### Performance Optimization

**Caching Strategy:**
- Redis caching for frequently accessed data
- HTTP response caching
- Database query result caching
- CDN for static assets (future)

**Database Optimization:**
- Query optimization and indexing
- Connection pooling
- Batch processing for bulk operations
- Archival strategy for old data

## Disaster Recovery

### Backup Strategy

**Database Backups:**
- Automated daily backups via Neon
- Point-in-time recovery capability
- Cross-region backup replication
- Backup verification and testing

**Application Backups:**
- Configuration backup
- Code repository backup
- Environment variable backup
- Deployment artifact backup

### Recovery Procedures

**Service Recovery:**
- Automated service restart policies
- Health check-based recovery
- Circuit breaker patterns
- Graceful degradation

**Data Recovery:**
- Database restore procedures
- Data validation after recovery
- Incremental recovery options
- Recovery time objectives (RTO < 1 hour)

## Future Architecture Considerations

### Microservices Evolution

**Service Decomposition:**
- Article ingestion service
- Publisher management service
- Category classification service
- Notification service
- Analytics service

### Event-Driven Architecture

**Event Streaming:**
- Apache Kafka or Redis Streams
- Event sourcing patterns
- CQRS implementation
- Real-time data processing

### Advanced Features

**Machine Learning Integration:**
- Content classification models
- Sentiment analysis pipeline
- Trend detection algorithms
- Recommendation engine

**Real-time Features:**
- WebSocket connections
- Server-sent events
- Real-time notifications
- Live data updates
