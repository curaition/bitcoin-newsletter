# Frontend Deployment Strategy

## Overview

This document outlines the deployment strategy for both the backoffice admin dashboard and consumer-facing frontend on Render, integrated with the existing FastAPI backend.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RENDER DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────────┤
│  Backend Services                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   FastAPI API   │  │  Celery Worker  │  │  Celery Beat    │ │
│  │   (Python)      │  │   (Python)      │  │   (Python)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  Frontend Services                                              │
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │   Backoffice    │  │   Consumer      │                     │
│  │   (React SPA)   │  │   (React SPA)   │                     │
│  └─────────────────┘  └─────────────────┘                     │
│                                                                 │
│  Data Services                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │   PostgreSQL    │  │     Redis       │                     │
│  │   (Database)    │  │    (Cache)      │                     │
│  └─────────────────┘  └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Frontend Applications

### 1. Backoffice Admin Dashboard

**Purpose**: Internal administration and monitoring
**URL**: `https://bitcoin-newsletter-backoffice.onrender.com`

**Features**:
- System health monitoring
- Article management
- Task scheduling and monitoring
- Database statistics
- Manual ingestion triggers
- User management (future)

**Tech Stack**:
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- React Query for API state management
- React Router for navigation
- Chart.js for metrics visualization

### 2. Consumer Frontend

**Purpose**: Public-facing newsletter and article access
**URL**: `https://bitcoin-newsletter-frontend.onrender.com`

**Features**:
- Newsletter subscription
- Article browsing and search
- Newsletter archive
- RSS feeds
- Mobile-responsive design
- SEO optimization

**Tech Stack**:
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- React Query for API state management
- React Router for navigation
- React Helmet for SEO

## Project Structure

```
bitcoin_newsletter/
├── backend/                    # Existing FastAPI backend
│   └── src/crypto_newsletter/
├── backoffice/                 # Admin dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── frontend/                   # Consumer frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── render.yaml                # Complete deployment config
```

## Deployment Process

### Phase 1: Backend Deployment (Already Planned)
1. Deploy FastAPI backend services
2. Verify API endpoints are working
3. Test health checks and admin endpoints

### Phase 2: Backoffice Frontend
1. Create React admin dashboard
2. Integrate with FastAPI admin endpoints
3. Deploy to Render as static site
4. Configure environment variables

### Phase 3: Consumer Frontend
1. Create React consumer application
2. Integrate with FastAPI public endpoints
3. Deploy to Render as static site
4. Configure SEO and performance optimization

## Environment Variables

### Backoffice
```bash
VITE_API_URL=https://bitcoin-newsletter-api.onrender.com
VITE_ENVIRONMENT=production
VITE_APP_NAME="Bitcoin Newsletter Admin"
```

### Consumer Frontend
```bash
VITE_API_URL=https://bitcoin-newsletter-api.onrender.com
VITE_ENVIRONMENT=production
VITE_APP_NAME="Bitcoin Newsletter"
VITE_GOOGLE_ANALYTICS_ID=GA_TRACKING_ID
```

## API Integration

### Admin Dashboard Endpoints
- `GET /admin/status` - System status
- `POST /admin/ingest` - Manual ingestion
- `GET /admin/stats` - System statistics
- `GET /health/detailed` - Detailed health check
- `GET /health/metrics` - System metrics

### Consumer Frontend Endpoints
- `GET /api/articles` - Article listing
- `GET /api/articles/{id}` - Article details
- `GET /api/newsletters` - Newsletter archive
- `POST /api/subscribe` - Newsletter subscription
- `GET /health` - Basic health check

## Development Workflow

### Local Development
```bash
# Backend
uv run crypto-newsletter serve --dev

# Backoffice (separate terminal)
cd backoffice
npm run dev

# Consumer Frontend (separate terminal)
cd frontend
npm run dev
```

### Build and Deploy
```bash
# Build both frontends
cd backoffice && npm run build
cd ../frontend && npm run build

# Deploy via Git push (Render auto-deploys)
git add .
git commit -m "Deploy frontend updates"
git push origin main
```

## Performance Considerations

### Static Site Optimization
- Code splitting with React.lazy()
- Image optimization and lazy loading
- Bundle size monitoring
- CDN caching via Render

### API Integration
- Request caching with React Query
- Error boundaries for API failures
- Loading states and skeleton screens
- Retry logic for failed requests

## Security

### Frontend Security
- Environment variable validation
- XSS protection via React
- HTTPS enforcement
- Content Security Policy headers

### API Security
- CORS configuration in FastAPI
- Rate limiting on API endpoints
- Input validation and sanitization
- Authentication tokens (future)

## Monitoring

### Frontend Monitoring
- Error tracking with Sentry (optional)
- Performance monitoring
- User analytics
- Build status monitoring

### Integration Monitoring
- API endpoint health checks
- Cross-origin request monitoring
- Service dependency tracking
- User experience metrics

## Cost Estimation

### Render Pricing (Monthly)
- FastAPI Backend: $7-25 (Starter to Standard)
- Celery Worker: $7-25 (Starter to Standard)
- Celery Beat: $7-25 (Starter to Standard)
- Backoffice Frontend: $0-7 (Free to Starter)
- Consumer Frontend: $0-7 (Free to Starter)
- PostgreSQL: $7-25 (Starter to Standard)
- Redis: $7-25 (Starter to Standard)

**Total Estimated Cost**: $35-139/month

### Optimization Options
- Use free tier for low-traffic frontends
- Combine services where possible
- Use existing Neon database
- Implement sleep mode for development

## Next Steps

1. **Complete Backend Deployment** (Current Phase)
2. **Create Backoffice React App** (Next Phase)
3. **Deploy Backoffice to Render**
4. **Create Consumer React App**
5. **Deploy Consumer Frontend to Render**
6. **Implement monitoring and analytics**
7. **Optimize performance and costs**
