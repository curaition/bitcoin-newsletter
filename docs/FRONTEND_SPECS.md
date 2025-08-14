# Frontend Implementation Specifications

This document captures the architectural decisions, best practices, and implementation standards for the Bitcoin Newsletter frontend applications. It serves as both a reference guide and a checklist to ensure consistency across all frontend development.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Shared Types Structure](#shared-types-structure)
- [Technology Stack Standards](#technology-stack-standards)
- [Implementation Best Practices](#implementation-best-practices)
- [Streamlined Foundation Checklist](#streamlined-foundation-checklist)
- [Deferred Features Tracking](#deferred-features-tracking)
- [Quality Standards](#quality-standards)
- [Deployment Configuration](#deployment-configuration)

---

## 🏗️ Architecture Overview

### Monorepo Structure
```
bitcoin_newsletter/                    # Root repository
├── backend/                          # Existing FastAPI backend
│   ├── src/crypto_newsletter/
│   ├── docs/
│   └── pyproject.toml
├── admin-dashboard/                  # React admin application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── consumer-frontend/                # Future React consumer app
│   └── (future implementation)
├── shared/                          # ✅ IMPLEMENTED
│   ├── types/                       # TypeScript type definitions
│   │   ├── api.ts                   # API types matching backend models
│   │   └── common.ts                # UI utility types
│   ├── utils/                       # Shared utilities
│   │   ├── type-guards.ts           # Runtime type validation
│   │   └── api-helpers.ts           # API utilities & error handling
│   └── README.md                    # Usage documentation
└── docs/                            # Project-wide documentation
    └── FRONTEND_SPECS.md            # This document
```

### Integration Patterns
- **Type Safety**: Shared TypeScript types between frontend and backend
- **API Integration**: Centralized API client with error handling
- **Authentication**: JWT with Clerk-compatible patterns for future migration
- **State Management**: TanStack Query for server state, Zustand for UI state
- **Component System**: Shadcn/ui with Tailwind CSS for consistent design

---

## 🔗 Shared Types Structure

### ✅ IMPLEMENTED: Core Type System

**Location**: `shared/types/`

#### API Types (`shared/types/api.ts`)
- **Domain Models**: `Article`, `Publisher`, `Category`, `User`
- **Request/Response**: `ArticleListParams`, `SystemStatusResponse`, `APIResponse<T>`
- **Authentication**: `LoginRequest`, `LoginResponse`, `User` (Clerk-compatible)
- **System Status**: `SystemHealthStatus`, `DatabaseStatus`, `CeleryStatus`

#### Common Types (`shared/types/common.ts`)
- **UI State**: `LoadingState`, `AsyncState<T>`, `PaginationState`
- **Forms**: `FormField<T>`, `ValidationResult`
- **Navigation**: `NavItem`, `Breadcrumb`
- **Tables**: `TableColumn<T>`, `TableState`

#### Type Guards (`shared/utils/type-guards.ts`)
- **Runtime Validation**: `isArticle()`, `isUser()`, `isSystemStatusResponse()`
- **Array Validation**: `isArticleArray()`, `isPublisherArray()`
- **Assertion Functions**: `assertIsArticle()`, `assertIsUser()`

#### API Helpers (`shared/utils/api-helpers.ts`)
- **URL Building**: `buildApiUrl()`, `buildArticleListUrl()`
- **Error Handling**: `APIError` class, `processApiResponse()`
- **Retry Logic**: `withRetry()`, `DEFAULT_RETRY_OPTIONS`
- **Pagination**: `calculatePagination()`, `getPaginationInfo()`

### Usage Pattern
```typescript
// Import types
import type { Article, SystemStatusResponse } from '../../../shared/types/api';

// Import utilities
import { isArticle, buildApiUrl, processApiResponse } from '../../../shared/utils/';

// Type-safe API integration
const result = await processApiResponse<Article[]>(response);
if (result.data && isArticleArray(result.data)) {
  setArticles(result.data); // Fully typed!
}
```

---

## 🛠️ Technology Stack Standards

### Core Framework
- **React 18.2+**: Latest stable with concurrent features
- **TypeScript 5.0+**: Strict mode enabled for full type safety
- **Vite 5.0+**: Fast development server and optimized builds

### UI Framework & Design ✅ **FULLY IMPLEMENTED**
- **Shadcn/ui**: High-quality, accessible React components
  - ✅ Configured with custom theme and design tokens
  - ✅ Components: Button, Card, Input, Badge, Table, Separator, Avatar
  - ✅ Proper TypeScript integration with variant types
- **Tailwind CSS 3.4+**: Utility-first CSS framework
  - ✅ Fully configured with PostCSS processing
  - ✅ Custom design system integration
  - ✅ Responsive breakpoints and utilities working
  - ✅ Dark/light theme support configured
- **Lucide React**: Consistent icon system
  - ✅ Integrated throughout navigation and UI components
- **Recharts**: React charting library (when needed)

### State Management & Data
- **TanStack Query v5**: Server state management and caching
- **Zustand**: Minimal client-side state (UI preferences only)
- **React Hook Form**: Form handling with validation
- **Zod**: Runtime type validation and schema definitions

### Routing & Navigation
- **React Router v6**: Client-side routing
- **Why not TanStack Router**: Overkill for 4-10 route admin dashboard

### Package Management
- **pnpm**: Faster installs and better disk usage than npm
- **Why not uv**: uv is Python-focused, not optimal for Node.js ecosystem

---

## 🎨 Day 3 Implementation Details

### ✅ **COMPLETED**: Tailwind CSS & Shadcn/ui Setup

#### Tailwind CSS Configuration
- **PostCSS Processing**: Fully configured and working
- **Design System**: Custom theme tokens integrated
- **Responsive Design**: Mobile-first approach with lg: breakpoints
- **Component Styling**: All UI components properly styled
- **Build Integration**: Vite processes Tailwind correctly

#### Shadcn/ui Component System
- **Base Components**: Button, Card, Input, Badge, Table, Separator, Avatar
- **Layout Components**: Responsive sidebar, header, navigation
- **Theme Integration**: Dark/light mode support configured
- **TypeScript Integration**: Full type safety with component variants
- **Accessibility**: ARIA labels and semantic HTML throughout

#### Layout Architecture
- **Desktop Layout**: Flexbox-based sidebar + main content
- **Mobile Layout**: Overlay sidebar with backdrop
- **Responsive Breakpoints**: Mobile-first with lg: desktop breakpoint
- **Navigation**: Active state indicators and smooth transitions

#### Key Fixes Applied
1. **Tailwind Processing**: Fixed PostCSS configuration for proper style compilation
2. **React Hydration**: Resolved SSR/client mismatch with Badge components
3. **Responsive Layout**: Fixed sidebar positioning with proper flex layout
4. **Component Spacing**: Added consistent margin/padding throughout UI

#### File Structure Created
```
admin-dashboard/src/
├── components/
│   ├── ui/                    # ✅ Shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── badge.tsx
│   │   ├── table.tsx
│   │   ├── separator.tsx
│   │   └── avatar.tsx
│   ├── layout/               # ✅ Layout components
│   │   ├── AppLayout.tsx     # Main responsive layout
│   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   ├── Header.tsx        # Top header bar
│   │   └── ProtectedRoute.tsx # Auth guard
│   └── common/               # ✅ Business components
│       └── LoadingSpinner.tsx
├── pages/                    # ✅ Route components
│   ├── dashboard/
│   │   └── DashboardPage.tsx # System overview
│   ├── articles/
│   │   └── ArticlesPage.tsx  # Article browser
│   ├── system/
│   │   └── SystemPage.tsx    # System controls
│   └── auth/
│       └── LoginPage.tsx     # Authentication
└── styles/
    └── globals.css           # ✅ Tailwind imports
```

---

## 📐 Implementation Best Practices

### 1. Component Organization
```typescript
// ✅ DO: Separate concerns clearly
admin-dashboard/src/
├── components/
│   ├── ui/                    # Shadcn/ui base components (don't modify)
│   ├── layout/               # Layout components (nav, sidebar, header)
│   ├── common/               # Reusable business components
│   └── forms/                # Form-specific components
├── pages/                    # Route components
├── hooks/                    # Custom hooks
├── services/                 # API clients and external services
└── stores/                   # Zustand stores (UI state only)
```

### 2. State Management Separation
```typescript
// ✅ DO: Clear separation of concerns
function ArticleList() {
  // Server state - use TanStack Query
  const { data: articles, isLoading } = useArticles();
  
  // UI state - use Zustand
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  
  // Local component state - use useState
  const [selectedArticles, setSelectedArticles] = useState<number[]>([]);
}

// ❌ DON'T: Mix server data in Zustand
const useStore = create((set) => ({
  articles: [], // DON'T - use TanStack Query instead
  sidebarOpen: false, // OK - UI state
}));
```

### 3. API Integration Patterns
```typescript
// ✅ DO: Use shared types and utilities
import type { Article } from '../../../shared/types/api';
import { buildApiUrl, processApiResponse } from '../../../shared/utils/api-helpers';

class AdminAPIClient {
  async getArticles(params: ArticleListParams): Promise<Article[]> {
    const url = buildApiUrl(this.baseUrl, '/api/articles', params);
    const response = await fetch(url, { headers: this.getHeaders() });
    const result = await processApiResponse<Article[]>(response);
    
    if (result.error) throw new Error(result.error.message);
    return result.data;
  }
}
```

### 4. Authentication Patterns (Clerk-Compatible)
```typescript
// ✅ DO: Use Clerk-compatible interface from day one
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoaded, setIsLoaded] = useState(false); // Clerk uses isLoaded
  
  // Clerk-compatible computed properties
  const isSignedIn = !!user;
  
  return { user, isSignedIn, isLoaded, signIn, signOut };
}

// Future migration to Clerk requires zero component changes:
// import { useAuth } from '@clerk/nextjs'; // Just change the import!
```

---

## ✅ Streamlined Foundation Checklist

### Week 1: Foundation Implementation

#### Day 1: Project Setup ✅ **COMPLETED**
- [x] Initialize Vite + React + TypeScript project
- [x] Install core dependencies (React Router, TanStack Query, Zustand)
- [x] Install UI dependencies (Shadcn/ui, Tailwind, Lucide React)
- [x] Configure Shadcn/ui with `components.json`
- [x] Set up basic project structure
- [x] Configure TypeScript with strict mode
- [x] Set up path aliases (`@/` for src)
- [x] Create core UI components (Button, Card, Input, Badge, Table)
- [x] Set up environment configuration
- [x] Test build and development server

#### Day 2: API Integration ✅ **COMPLETED**
- [x] Create API client class with shared types integration
- [x] Implement JWT authentication (Clerk-compatible patterns)
- [x] Set up TanStack Query configuration
- [x] Create authentication hooks (`useAuth`)
- [x] Test connection to existing FastAPI backend
- [x] Implement error handling patterns
- [x] Create API hooks for articles and system status
- [x] Set up query invalidation and caching
- [x] Create comprehensive test panel

#### Day 3: Layout & Routing ✅ **COMPLETED**
- [x] Create protected route component with authentication guards
- [x] Implement main application layout (responsive sidebar, header)
- [x] Set up React Router with 4 core routes (/dashboard, /articles, /system, /login)
- [x] Create navigation components with active state indicators
- [x] Implement responsive design patterns (mobile overlay, desktop flex layout)
- [x] Add loading states and error boundaries
- [x] **BONUS**: Fixed Tailwind CSS processing and React hydration issues
- [x] **BONUS**: Implemented complete UI component system with Shadcn/ui

#### Day 4: Polish & Error Handling ✅ **COMPLETED**
- [x] Implement consistent error handling with user-friendly messages
- [x] Add loading states for all async operations (skeleton animations)
- [x] Create reusable UI components (StatusCard, LoadingSpinner, etc.)
- [x] Set up environment configuration with proper API integration
- [x] Add basic accessibility features (ARIA labels, semantic HTML)
- [x] Test responsive design (mobile overlay, desktop flex layout)
- [x] **BONUS**: Real API integration with live data from backend
- [x] **BONUS**: Horizontal breadcrumb navigation system
- [x] **BONUS**: Manual ingestion with proper error handling

#### Day 5: Publisher Resolution & Article Details ⏳ **IN PROGRESS**
- [ ] Implement publisher name resolution (replace Publisher ID: X with actual names)
- [ ] Create Article Detail Page with full content display
- [ ] Add article navigation (previous/next article)
- [ ] Implement backend search parameter support
- [ ] Add advanced filtering (by publisher, date range, status)
- [ ] Performance optimizations and caching improvements

### Week 2: MVP Dashboard Features ✅ **COMPLETED**

#### Day 1: Dashboard Overview ✅ **COMPLETED**
- [x] System health status cards (API, Database, Task Queue, Environment)
- [x] Recent activity display (real system events)
- [x] Quick action buttons (manual ingestion, system refresh)
- [x] Real-time status updates (30s interval with TanStack Query)

#### Day 2: Article Browser ✅ **COMPLETED**
- [x] Article table with pagination (20 articles per page)
- [x] Search and filter functionality (debounced search input)
- [x] Publisher filter dropdown (showing Publisher ID: X format)
- [x] Responsive table design (mobile-friendly layout)

#### Day 3: Article Detail View ⏳ **PARTIALLY COMPLETED**
- [x] Full article content display (working with real data)
- [x] Metadata and processing information (status, word count, dates)
- [ ] Navigation between articles (previous/next buttons)
- [x] External link handling (View Original button)

#### Day 4: System Status & Controls ✅ **COMPLETED**
- [x] Detailed system status page (comprehensive health monitoring)
- [x] Manual ingestion trigger (with proper error handling)
- [x] Recent system activity log (real events from backend)
- [x] Error monitoring display (user-friendly error messages)

---

## 🚨 Deferred Features Tracking

### From Foundation PRD (Add Later)

#### Testing & Quality (Priority: Medium)
- [ ] **Vitest Setup**: Unit testing framework
- [ ] **Testing Library**: Component testing utilities
- [ ] **E2E Testing**: Playwright for critical user flows
- [ ] **Coverage Reports**: >80% coverage target

#### Development Tools (Priority: Low)
- [ ] **Husky Git Hooks**: Pre-commit linting and formatting
- [ ] **Bundle Analysis**: Webpack bundle analyzer
- [ ] **Performance Monitoring**: Lighthouse CI integration
- [ ] **Storybook**: Component documentation (if team grows)

#### Advanced Features (Priority: Future)
- [ ] **PWA Configuration**: Service worker, offline support
- [ ] **WebSocket Integration**: Real-time updates
- [ ] **Advanced Error Boundaries**: Error reporting service
- [ ] **Internationalization**: i18n support if needed

#### Security & Monitoring (Priority: High - Add Soon)
- [ ] **Content Security Policy**: CSP headers
- [ ] **Error Reporting**: Sentry or similar service
- [ ] **Performance Monitoring**: Real user monitoring
- [ ] **Accessibility Testing**: Automated a11y checks

### Enhancement Triggers

**Add Testing When**:
- Team size > 1 developer
- Critical bugs appear in production
- Refactoring becomes frequent

**Add Advanced Tooling When**:
- Build times exceed 30 seconds
- Bundle size exceeds 1MB
- Performance issues reported

**Add Monitoring When**:
- User base > 10 active users
- Production errors occur
- Performance optimization needed

---

## 🎯 Quality Standards

### Performance Requirements
- **Initial Load**: <3 seconds on 3G connection
- **Route Navigation**: <500ms between pages
- **API Response Handling**: <2 seconds for most operations
- **Bundle Size**: <500KB initial bundle

### Code Quality
- **TypeScript**: Strict mode, zero `any` types in production
- **ESLint**: Zero linting errors in builds
- **Prettier**: Consistent code formatting
- **Component Size**: <200 lines per component (split if larger)

### Accessibility
- **WCAG 2.1 AA**: Minimum compliance level
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Color Contrast**: 4.5:1 minimum ratio

### Browser Support
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+
- **JavaScript**: ES2020 features supported

---

## 🚀 Deployment Configuration

### Render Service Configuration
```yaml
# render.yaml (add to existing backend services)
services:
  - type: web
    name: bitcoin-newsletter-admin
    env: node
    plan: starter
    buildCommand: cd admin-dashboard && pnpm install && pnpm run build
    startCommand: cd admin-dashboard && pnpm run preview
    envVars:
      - key: VITE_API_URL
        value: https://bitcoin-newsletter-api.onrender.com
      - key: VITE_APP_ENV
        value: production
      - key: VITE_AUTH_PROVIDER
        value: jwt
```

### Environment Variables
```bash
# .env.example
VITE_API_URL=https://bitcoin-newsletter-api.onrender.com
VITE_WS_URL=wss://bitcoin-newsletter-api.onrender.com
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=production
VITE_AUTH_PROVIDER=jwt

# .env.local (development)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_ENV=development
```

### CORS Configuration (Backend)
```python
# backend/src/crypto_newsletter/web/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development
        "https://bitcoin-newsletter-admin.onrender.com"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 Maintenance Guidelines

### When to Update This Document
- [ ] New architectural decisions made
- [ ] Technology stack changes
- [ ] Best practices evolve
- [ ] Deferred features are implemented
- [ ] Quality standards change

### Regular Reviews
- **Monthly**: Review deferred features for implementation priority
- **Quarterly**: Assess technology stack for updates
- **After Major Features**: Update best practices based on learnings

### Version Control
- Document version in git commits
- Link to relevant PRDs and implementation decisions
- Maintain changelog of significant updates

---

## 👨‍💻 New Developer Onboarding Summary

### 🚀 **Current Status (Day 3 Complete)**

The admin dashboard is **fully functional** with a complete UI foundation. Here's what's ready:

#### ✅ **What's Working**
1. **Complete UI System**: Tailwind CSS + Shadcn/ui fully configured and styled
2. **Responsive Layout**: Mobile overlay + desktop flex layout working perfectly
3. **Authentication**: JWT-based auth with Clerk-compatible patterns
4. **API Integration**: TanStack Query + shared types for type-safe backend communication
5. **Navigation**: React Router with 4 core routes and protected routes
6. **Component Library**: Reusable UI components with consistent styling

#### 🎯 **Quick Start for New Developers**

```bash
# 1. Install dependencies
cd admin-dashboard
pnpm install

# 2. Start development server
pnpm run dev

# 3. Visit http://localhost:3000
# Login with: admin@example.com / password123
```

#### 📱 **Current Pages**
- **`/dashboard`**: System overview with status cards and quick actions
- **`/articles`**: Article browser with search and filters (mock data)
- **`/system`**: System controls and monitoring (mock data)
- **`/login`**: Authentication page with form validation

#### 🛠️ **Tech Stack in Use**
- **React 18.2** + **TypeScript 5.0** + **Vite 5.0**
- **Tailwind CSS 3.4** (fully configured and working)
- **Shadcn/ui** (complete component system)
- **React Router v6** (client-side routing)
- **TanStack Query v5** (server state management)
- **Zustand** (UI state management)

#### 🔧 **Key Configuration Files**
- `tailwind.config.js` - Tailwind configuration with custom theme
- `components.json` - Shadcn/ui configuration
- `vite.config.ts` - Build configuration with path aliases
- `tsconfig.json` - TypeScript strict mode configuration

#### 📋 **Next Steps (Day 4)**
1. **Connect Real Data**: Replace mock data with actual API calls
2. **Add Functionality**: Implement search, filters, and action buttons
3. **Error Handling**: Add comprehensive error boundaries and user feedback
4. **Polish**: Loading states, animations, and accessibility improvements

#### 🐛 **Known Issues: NONE**
All major issues have been resolved:
- ✅ Tailwind CSS processing fixed
- ✅ React hydration errors resolved
- ✅ Responsive layout working correctly
- ✅ Component styling fully functional

---

## 🎉 Day 4 COMPLETE - Real Data Integration & Polish ✅

### ✅ Major Achievements

**Real API Integration**
- Dashboard connected to live system status (`/admin/status`)
- Articles page displaying real data from `/api/articles` (39 articles)
- Search functionality with debouncing and API integration
- Manual ingestion with proper error handling and user feedback

**Enhanced User Experience**
- Loading states with skeleton animations for all async operations
- Comprehensive error handling with user-friendly messages
- Success/error alerts for manual ingestion and system operations
- Responsive design working perfectly on mobile and desktop

**Technical Improvements**
- Fixed React object rendering errors (Celery task status objects)
- Updated shared types to match actual API response structure
- Implemented proper data transformation for API compatibility
- Added StatusCard component for consistent status display

**Functional Features**
- Real-time system health monitoring (API, Database, Task Queue, Environment)
- Article browsing with search, pagination, and filtering
- Manual ingestion triggers with loading states and error feedback
- Navigation between Dashboard, Articles, and System pages

### 🔧 Current System Status
- **Backend Running**: FastAPI server on localhost:8000 ✅
- **Frontend Running**: Vite dev server on localhost:3000 ✅
- **Database Connected**: 39 articles in Neon PostgreSQL ✅
- **System Status**: API responding with real health data ✅
- **Scheduled Tasks**: Celery Beat running 4-hour ingestion cycles ✅

### 🐛 Data Discrepancy Investigation Required

**CRITICAL ISSUE IDENTIFIED**: System Activity shows "Scheduled ingestion completed 2 hours ago with 3 articles processed successfully" but Articles page shows most recent article is from ~10 hours ago.

**Possible Causes**:
1. **Database Transaction Issues**: Articles processed but not committed to database
2. **Timezone Mismatch**: Backend/frontend displaying different timezones
3. **Caching Issues**: Frontend showing stale data despite successful ingestion
4. **API Response Mismatch**: System activity and articles endpoints returning different data
5. **Processing Pipeline Issue**: Articles ingested but not properly saved/indexed

**Investigation Required**:
- Check backend logs for recent ingestion attempts
- Verify database state directly (recent articles in DB)
- Compare system activity timestamps with article timestamps
- Validate API response consistency between endpoints

### 🚀 Day 5 Handoff - Publisher Resolution & Data Integrity

**Priority 1: Data Investigation**
- Resolve discrepancy between system activity and article timestamps
- Verify scheduled ingestion is properly saving articles to database
- Ensure data consistency across all API endpoints

**Priority 2: Publisher Resolution**
- Implement publisher name resolution (replace "Publisher ID: X" with actual names)
- Add publisher lookup table/endpoint integration
- Update Article Detail Page with proper publisher information

**Priority 3: Enhanced Features**
- Create comprehensive Article Detail Page with full content display
- Add article navigation (previous/next article buttons)
- Implement backend search parameter support
- Add advanced filtering (by publisher, date range, status)

**Ready for Handoff**: All foundation work complete, real data integration working, investigation path clearly defined for data discrepancy issue.

---

## 📊 Comprehensive Day 4 Summary

### ✅ **CONFIRMED COMPLETE**

**Foundation (Days 1-3)**
- Project setup with Vite + React + TypeScript ✅
- Shared types system with API integration ✅
- Tailwind CSS + Shadcn/ui component system ✅
- Authentication with JWT (Clerk-compatible) ✅
- React Router with protected routes ✅
- TanStack Query for server state management ✅

**Day 4 Real Data Integration**
- Live API connection to FastAPI backend ✅
- Real system health monitoring ✅
- Article browsing with 39 real articles ✅
- Search functionality with debouncing ✅
- Manual ingestion triggers ✅
- Comprehensive error handling ✅
- Loading states and user feedback ✅

### ⏳ **DAY 5 TASKS IDENTIFIED**

**None of Day 5's original tasks have been completed yet.** Day 4 focused on real data integration and polish, which was more extensive than originally planned.

**Day 5 Priority Tasks**:
1. **Data Investigation**: Resolve timestamp discrepancy between system activity and articles
2. **Publisher Resolution**: Replace "Publisher ID: X" with actual publisher names
3. **Article Detail Enhancement**: Add navigation between articles
4. **Backend Integration**: Implement search parameter support
5. **Advanced Features**: Date range filtering, performance optimizations

### 🔍 **CRITICAL INVESTIGATION NEEDED**

The data discrepancy issue (system shows recent ingestion success but articles appear old) must be resolved before proceeding with Day 5 features. This indicates a potential data integrity issue that could affect all future development.

---

*Document Version: 4.0*
*Last Updated: August 14, 2025 - Day 4 Complete, Day 5 Ready*
*Status: Living Document - Day 4 Complete, Data Investigation Required*
*Related PRDs: Back Office Foundation PRD, Simple Admin Dashboard MVP PRD*
