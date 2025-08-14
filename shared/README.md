# Shared Types and Utilities

This directory contains TypeScript types and utilities shared between the backend and frontend applications.

## Structure

```
shared/
├── types/
│   ├── api.ts           # API request/response types matching backend models
│   └── common.ts        # Common utility types for UI and business logic
├── utils/
│   ├── type-guards.ts   # Runtime type checking and validation
│   └── api-helpers.ts   # API utilities, URL building, error handling
└── README.md           # This file
```

## Usage

### Frontend (React Admin Dashboard)

```typescript
// Import types
import type { Article, SystemStatusResponse } from '../../../shared/types/api';
import type { LoadingState, AsyncState } from '../../../shared/types/common';

// Import utilities
import { isArticle, validateArticleForDisplay } from '../../../shared/utils/type-guards';
import { buildApiUrl, processApiResponse } from '../../../shared/utils/api-helpers';

// Use in components
function ArticleList() {
  const [articles, setArticles] = useState<Article[]>([]);
  
  // Type-safe API call
  const fetchArticles = async () => {
    const url = buildApiUrl(API_BASE_URL, '/api/articles', { limit: 20 });
    const response = await fetch(url);
    const result = await processApiResponse<Article[]>(response);
    
    if (result.data && isArticleArray(result.data)) {
      setArticles(result.data);
    }
  };
}
```

### Backend (FastAPI)

```python
# The types in api.ts should match your Pydantic models
# Example: src/crypto_newsletter/shared/models/models.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class Article(BaseModel):
    id: int
    guid: str
    title: str
    url: str
    body: Optional[str] = None
    # ... matches Article interface in api.ts
```

## Type Synchronization

### Manual Synchronization (Current)

1. **Backend Changes**: When you modify Pydantic models in the backend
2. **Update Types**: Manually update the corresponding TypeScript interfaces in `shared/types/api.ts`
3. **Validate**: Use type guards in `shared/utils/type-guards.ts` to ensure runtime type safety

### Future: Automatic Generation

Consider tools like:
- **openapi-typescript**: Generate TypeScript types from OpenAPI schema
- **quicktype**: Generate types from JSON samples
- **Custom script**: Parse Pydantic models and generate TypeScript

## Best Practices

### 1. Type Naming Conventions

```typescript
// Match backend model names exactly
interface Article { }        // ✅ Matches backend Article model
interface ArticleData { }    // ❌ Don't add suffixes unless necessary

// Use descriptive names for request/response types
interface ArticleListParams { }     // ✅ Clear purpose
interface ArticleListResponse { }   // ✅ Clear purpose
```

### 2. Optional vs Required Fields

```typescript
// Match backend model field requirements exactly
interface Article {
  id: number;              // Required in backend
  title: string;           // Required in backend
  body: string | null;     // Optional in backend, can be null
  summary?: string;        // Optional in backend, may not be present
}
```

### 3. Date Handling

```typescript
// Always use ISO 8601 strings for API communication
interface Article {
  created_at: string;      // ISO 8601 datetime string
  published_on: string;    // ISO 8601 datetime string
}

// Convert to Date objects in frontend when needed
const article: Article = await fetchArticle();
const publishedDate = new Date(article.published_on);
```

### 4. Error Handling

```typescript
// Use consistent error structure
interface APIError {
  message: string;         // Human-readable error message
  code?: string;          // Machine-readable error code
  details?: Record<string, any>; // Additional error context
  status?: number;        // HTTP status code
}

// Always handle both success and error cases
const result = await processApiResponse<Article>(response);
if (result.error) {
  console.error('API Error:', result.error.message);
  return;
}
// result.data is guaranteed to exist here
```

### 5. Type Guards Usage

```typescript
// Always validate API responses
const response = await fetch('/api/articles');
const data = await response.json();

// ❌ Don't trust API responses
const articles: Article[] = data; // Unsafe!

// ✅ Validate with type guards
if (isArticleArray(data)) {
  const articles: Article[] = data; // Type-safe!
} else {
  console.error('Invalid article data received');
}
```

## Maintenance

### When Backend Models Change

1. **Update `shared/types/api.ts`** with new field definitions
2. **Update type guards** in `shared/utils/type-guards.ts` if needed
3. **Update API helpers** in `shared/utils/api-helpers.ts` if new endpoints are added
4. **Test frontend** to ensure no TypeScript errors
5. **Update validation** logic if field requirements change

### When Adding New Features

1. **Add types** to appropriate files (`api.ts` for API-related, `common.ts` for UI-related)
2. **Add type guards** for runtime validation
3. **Add utilities** for common operations
4. **Document** usage patterns in this README

## Integration Examples

### API Client Integration

```typescript
// admin-dashboard/src/services/api.ts
import type { Article, ArticleListParams, SystemStatusResponse } from '../../../shared/types/api';
import { buildApiUrl, processApiResponse, createAuthHeaders } from '../../../shared/utils/api-helpers';
import { isArticleArray, isSystemStatusResponse } from '../../../shared/utils/type-guards';

export class AdminAPIClient {
  constructor(private baseUrl: string, private getToken: () => string | null) {}

  async getArticles(params: ArticleListParams = {}): Promise<Article[]> {
    const url = buildApiUrl(this.baseUrl, '/api/articles', params);
    const headers = createAuthHeaders(this.getToken());
    
    const response = await fetch(url, { headers });
    const result = await processApiResponse<Article[]>(response);
    
    if (result.error) {
      throw new Error(result.error.message);
    }
    
    if (!isArticleArray(result.data)) {
      throw new Error('Invalid article data received');
    }
    
    return result.data;
  }
}
```

### React Hook Integration

```typescript
// admin-dashboard/src/hooks/useArticles.ts
import { useQuery } from '@tanstack/react-query';
import type { Article, ArticleListParams } from '../../../shared/types/api';
import { createCacheKey } from '../../../shared/utils/api-helpers';
import { apiClient } from '../services/api';

export function useArticles(params: ArticleListParams = {}) {
  return useQuery({
    queryKey: ['articles', createCacheKey('list', params)],
    queryFn: () => apiClient.getArticles(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```
