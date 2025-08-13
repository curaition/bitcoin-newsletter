# API Reference

This document provides comprehensive documentation for the Bitcoin Newsletter REST API.

## Base URL

- **Production**: `https://bitcoin-newsletter-api.onrender.com`
- **Development**: `http://localhost:8000`

## Authentication

Currently, the API is publicly accessible. Authentication will be added in future versions.

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Burst**: Up to 200 requests in a 1-minute window
- **Headers**: Rate limit information is included in response headers

## Response Format

All API responses follow a consistent JSON format:

```json
{
  "data": {},
  "message": "Success",
  "timestamp": "2025-01-10T12:00:00Z",
  "status": "success"
}
```

## Error Handling

Error responses include detailed information:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {}
  },
  "timestamp": "2025-01-10T12:00:00Z",
  "status": "error"
}
```

## Endpoints

### Health Check Endpoints

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00Z",
  "version": "1.0.0"
}
```

#### GET /health/detailed
Comprehensive health check with component status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T12:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "external_apis": {
      "coindesk": {
        "status": "healthy",
        "response_time_ms": 120
      }
    }
  }
}
```

### Article Endpoints

#### GET /api/articles
Retrieve articles with optional filtering and pagination.

**Query Parameters:**
- `limit` (integer, optional): Number of articles to return (default: 20, max: 100)
- `offset` (integer, optional): Number of articles to skip (default: 0)
- `hours` (integer, optional): Filter articles from last N hours
- `publisher` (string, optional): Filter by publisher name
- `category` (string, optional): Filter by category (BTC, ETH, TRADING, etc.)
- `search` (string, optional): Search in title and content
- `sort` (string, optional): Sort order (newest, oldest, popular)

**Example Request:**
```
GET /api/articles?limit=10&hours=24&category=BTC&sort=newest
```

**Response:**
```json
{
  "data": {
    "articles": [
      {
        "id": 1,
        "external_id": 12345,
        "title": "Bitcoin Reaches New All-Time High",
        "subtitle": "Market analysis shows bullish trends",
        "url": "https://coindesk.com/article-12345",
        "published_on": "2025-01-10T10:00:00Z",
        "authors": "John Doe, Jane Smith",
        "publisher": {
          "id": 1,
          "name": "CoinDesk",
          "url": "https://coindesk.com"
        },
        "categories": [
          {
            "id": 1,
            "name": "Bitcoin",
            "category": "BTC"
          }
        ],
        "engagement": {
          "upvotes": 15,
          "downvotes": 3,
          "score": 12
        },
        "sentiment": "POSITIVE"
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 10,
      "offset": 0,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### GET /api/articles/{id}
Retrieve a specific article by ID.

**Path Parameters:**
- `id` (integer): Article ID

**Response:**
```json
{
  "data": {
    "id": 1,
    "external_id": 12345,
    "guid": "article-guid-12345",
    "title": "Bitcoin Reaches New All-Time High",
    "subtitle": "Market analysis shows bullish trends",
    "url": "https://coindesk.com/article-12345",
    "body": "Full article content...",
    "published_on": "2025-01-10T10:00:00Z",
    "created_at": "2025-01-10T10:05:00Z",
    "updated_at": "2025-01-10T10:05:00Z",
    "authors": "John Doe, Jane Smith",
    "keywords": "bitcoin,cryptocurrency,trading",
    "language": "EN",
    "image_url": "https://coindesk.com/images/article-12345.jpg",
    "publisher": {
      "id": 1,
      "name": "CoinDesk",
      "key": "coindesk",
      "url": "https://coindesk.com",
      "language": "EN"
    },
    "categories": [
      {
        "id": 1,
        "name": "Bitcoin",
        "category": "BTC"
      }
    ],
    "engagement": {
      "upvotes": 15,
      "downvotes": 3,
      "score": 12
    },
    "sentiment": "POSITIVE",
    "status": "ACTIVE"
  }
}
```

### Statistics Endpoints

#### GET /api/stats
Get article statistics and metrics.

**Response:**
```json
{
  "data": {
    "total_articles": 1250,
    "recent_articles_24h": 45,
    "active_publishers": 5,
    "categories_count": 10,
    "last_updated": "2025-01-10T12:00:00Z",
    "top_publishers": [
      {
        "publisher": "CoinDesk",
        "count": 500
      },
      {
        "publisher": "CoinTelegraph",
        "count": 350
      }
    ],
    "top_categories": [
      {
        "category": "Bitcoin",
        "count": 600
      },
      {
        "category": "Trading",
        "count": 400
      }
    ],
    "recent_activity": {
      "last_ingestion": "2025-01-10T08:00:00Z",
      "articles_processed_today": 45,
      "success_rate": 0.95
    }
  }
}
```

### Publisher Endpoints

#### GET /api/publishers
List all publishers.

**Response:**
```json
{
  "data": {
    "publishers": [
      {
        "id": 1,
        "name": "CoinDesk",
        "key": "coindesk",
        "url": "https://coindesk.com",
        "language": "EN",
        "article_count": 500,
        "last_article": "2025-01-10T10:00:00Z"
      }
    ]
  }
}
```

### Category Endpoints

#### GET /api/categories
List all categories with article counts.

**Response:**
```json
{
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "Bitcoin",
        "category": "BTC",
        "article_count": 600
      },
      {
        "id": 2,
        "name": "Ethereum",
        "category": "ETH",
        "article_count": 300
      }
    ]
  }
}
```

### Admin Endpoints

#### GET /admin/status
Administrative status endpoint with detailed system information.

**Response:**
```json
{
  "data": {
    "system": {
      "status": "operational",
      "uptime": "5d 12h 30m",
      "version": "1.0.0",
      "environment": "production"
    },
    "services": {
      "web": "healthy",
      "worker": "healthy",
      "beat": "healthy",
      "redis": "healthy"
    },
    "database": {
      "status": "healthy",
      "connections": 5,
      "total_articles": 1250,
      "last_migration": "2025-01-01T00:00:00Z"
    },
    "tasks": {
      "active": 2,
      "scheduled": 1,
      "failed_24h": 0
    },
    "ingestion": {
      "last_run": "2025-01-10T08:00:00Z",
      "next_run": "2025-01-10T12:00:00Z",
      "success_rate": 0.95,
      "articles_today": 45
    }
  }
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Response Headers

All responses include these headers:

- `X-Request-ID`: Unique request identifier
- `X-Response-Time`: Response time in milliseconds
- `X-Rate-Limit-Remaining`: Remaining requests in current window
- `X-Rate-Limit-Reset`: Time when rate limit resets

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## SDK and Examples

### Python Example

```python
import requests

# Get recent articles
response = requests.get(
    "https://bitcoin-newsletter-api.onrender.com/api/articles",
    params={
        "limit": 10,
        "hours": 24,
        "category": "BTC"
    }
)

articles = response.json()["data"]["articles"]
for article in articles:
    print(f"{article['title']} - {article['published_on']}")
```

### JavaScript Example

```javascript
// Fetch recent Bitcoin articles
fetch('https://bitcoin-newsletter-api.onrender.com/api/articles?category=BTC&limit=5')
  .then(response => response.json())
  .then(data => {
    data.data.articles.forEach(article => {
      console.log(`${article.title} - ${article.published_on}`);
    });
  });
```

### cURL Example

```bash
# Get system health
curl -X GET "https://bitcoin-newsletter-api.onrender.com/health/detailed"

# Get recent articles
curl -X GET "https://bitcoin-newsletter-api.onrender.com/api/articles?limit=5&hours=24"

# Get specific article
curl -X GET "https://bitcoin-newsletter-api.onrender.com/api/articles/1"
```

## Webhooks (Future)

Webhook endpoints will be available for real-time notifications:

- `POST /webhooks/article-published`: New article notifications
- `POST /webhooks/system-alert`: System alert notifications

## Changelog

### v1.0.0 (Current)
- Initial API release
- Article retrieval endpoints
- Health check endpoints
- Statistics endpoints
- Admin status endpoint

### Future Versions
- Authentication and authorization
- Webhook support
- GraphQL endpoint
- Real-time WebSocket connections
- Advanced filtering and search
