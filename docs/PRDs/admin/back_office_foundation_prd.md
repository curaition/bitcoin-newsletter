# Back Office Frontend Foundation
## Product Requirements Document (PRD)

### Executive Summary
Establishes the foundational architecture, development environment, and core infrastructure for the React-based admin dashboard. This PRD defines the technical foundation that all subsequent back office PRDs will build upon.

---

## 1. Product Overview

### Vision
Create a robust, scalable frontend foundation that enables rapid development of admin dashboard features while maintaining code quality, performance, and maintainability.

### Core Value Proposition
- **Rapid Feature Development**: Standardized patterns and components for quick feature implementation
- **Consistent User Experience**: Unified design system and interaction patterns
- **Scalable Architecture**: Foundation that supports complex admin features without technical debt
- **Developer Productivity**: Modern tooling and development experience
- **Integration Ready**: Seamless connection to existing FastAPI backend

### Current State Assessment
**Existing Backend Infrastructure**:
- ✅ FastAPI with 21 routes at https://bitcoin-newsletter-api.onrender.com
- ✅ Admin endpoints (/admin/status, /admin/ingest, /admin/health)
- ✅ Article API (/api/articles) with authentication
- ✅ Neon PostgreSQL with structured data
- ✅ JWT authentication system
- ✅ CORS configuration for API access

**Missing Frontend Infrastructure**:
- ❌ No React application
- ❌ No UI component system
- ❌ No API integration layer
- ❌ No authentication flow
- ❌ No deployment pipeline

---

## 2. Technical Architecture

### Technology Stack Selection

#### Core Framework
- **React 18.2+**: Latest stable version with concurrent features
- **TypeScript 5.0+**: Full type safety and developer experience
- **Vite 5.0+**: Fast development and optimized production builds

#### UI Framework & Design
- **Shadcn/ui**: High-quality, accessible React components
- **Tailwind CSS 3.4+**: Utility-first CSS framework
- **Lucide React**: Consistent icon system
- **Recharts**: React charting library for analytics

#### Routing & Navigation
- **React Router v6**: Client-side routing and navigation
  - **Why not TanStack Router?** Overkill for our 4-10 route admin dashboard
  - **Scaling path**: React Router handles complex nested routing when AI features are added

#### State Management & Data
- **TanStack Query v5**: Server state management and caching
  - **Why essential**: Automatic caching, loading states, background refetching
  - **Use for**: All API calls to FastAPI backend
- **Zustand**: Client-side state management
  - **Why minimal**: Simple stores for UI state (sidebar, theme, user preferences)
  - **Use for**: Local UI state that doesn't persist to server
- **React Hook Form**: Form handling with validation
- **Zod**: Runtime type validation and schema definitions

#### Development & Build Tools
- **ESLint + Prettier**: Code linting and formatting
- **Husky**: Git hooks for code quality
- **TypeScript**: Static type checking
- **Vite PWA Plugin**: Progressive Web App capabilities

### Project Structure
```
back-office-frontend/
├── public/
│   ├── favicon.ico
│   ├── logo.svg
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── ui/                    # Shadcn/ui base components
│   │   ├── layout/               # Layout components (nav, sidebar, header)
│   │   ├── forms/                # Reusable form components
│   │   ├── charts/               # Chart components for analytics
│   │   ├── data-tables/          # Table components with sorting/filtering
│   │   └── common/               # Shared utility components
│   ├── pages/
│   │   ├── auth/                 # Authentication pages
│   │   ├── dashboard/            # Main dashboard pages
│   │   ├── content/              # Content management pages
│   │   ├── monitoring/           # System monitoring pages
│   │   ├── analytics/            # Analytics and reporting pages
│   │   └── settings/             # Settings and configuration pages
│   ├── hooks/
│   │   ├── api/                  # API-specific hooks
│   │   ├── auth/                 # Authentication hooks
│   │   └── common/               # Utility hooks
│   ├── services/
│   │   ├── api/                  # API client and service functions
│   │   ├── auth/                 # Authentication services
│   │   └── storage/              # Local storage utilities
│   ├── stores/
│   │   ├── auth.ts               # Authentication state
│   │   ├── ui.ts                 # UI state (sidebar, theme, etc.)
│   │   └── settings.ts           # User preferences
│   ├── types/
│   │   ├── api.ts                # API response types
│   │   ├── auth.ts               # Authentication types
│   │   └── common.ts             # Shared types
│   ├── utils/
│   │   ├── api.ts                # API utilities
│   │   ├── format.ts             # Data formatting utilities
│   │   ├── validation.ts         # Validation schemas
│   │   └── constants.ts          # Application constants
│   ├── styles/
│   │   ├── globals.css           # Global styles and Tailwind imports
│   │   └── components.css        # Component-specific styles
│   ├── App.tsx                   # Main application component
│   ├── main.tsx                  # Application entry point
│   └── vite-env.d.ts            # Vite type definitions
├── .env.example                  # Environment variables template
├── .env.local                    # Local development environment
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── components.json               # Shadcn/ui configuration
└── README.md
```

---

## 3. Functional Requirements

### 3.1 Development Environment Setup
**Primary Responsibility**: Establish consistent, efficient development workflow

**Core Setup Requirements**:
- **Project Initialization**: Vite + React + TypeScript template
- **UI Component System**: Shadcn/ui installation and configuration
- **Code Quality Tools**: ESLint, Prettier, Husky setup
- **Environment Configuration**: Development, staging, production environments
- **Build Pipeline**: Optimized production builds with code splitting

**Technical Requirements**:
- Node.js 18+ compatibility
- Fast development server (<1 second startup)
- Hot module replacement for instant feedback
- TypeScript strict mode enabled
- Automated code formatting on save

**Success Criteria**:
- New developer setup in <15 minutes
- Development server starts in <2 seconds
- Type checking completes in <5 seconds
- Production build completes in <30 seconds

### 3.2 API Integration Foundation
**Primary Responsibility**: Establish robust connection to existing FastAPI backend

**Core Integration Requirements**:
- **API Client**: Centralized HTTP client with error handling
- **Authentication Flow**: JWT token management and renewal
- **Request/Response Types**: Full TypeScript definitions
- **Error Handling**: Consistent error response processing
- **Loading States**: Standardized loading and error UI patterns

**Technical Implementation**:
```typescript
// API Client Configuration
class AdminAPIClient {
  private baseURL: string;
  private authToken: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  async request<T>(
    endpoint: string, 
    options: RequestOptions = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
      });

      if (!response.ok) {
        throw new APIError(response.status, await response.text());
      }

      const data = await response.json();
      return { data, status: response.status };
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(0, 'Network error');
    }
  }

  // Specific API methods
  async getSystemStatus() {
    return this.request<SystemStatus>('/admin/status');
  }

  async getArticles(params: ArticleParams) {
    const query = new URLSearchParams(params).toString();
    return this.request<ArticleResponse>(`/api/articles?${query}`);
  }

  async triggerIngestion() {
    return this.request<IngestionResult>('/admin/ingest', { method: 'POST' });
  }
}
```

**Success Criteria**:
- All existing API endpoints accessible
- Automatic authentication token refresh
- Consistent error handling across all requests
- Type-safe API responses

### 3.3 Authentication & Authorization Foundation
**Primary Responsibility**: Secure access control with seamless Clerk migration path

**PoC Authentication Strategy**:
- **Current**: Simple JWT authentication with hardcoded admin credentials
- **Future**: Direct migration to Clerk with zero frontend refactoring
- **Pattern**: Clerk-compatible hooks and component patterns from day one

**Core Authentication Requirements**:
- **Login Flow**: Username/password authentication with JWT tokens
- **Token Management**: Automatic token storage and validation
- **Route Protection**: Unauthorized access prevention using Clerk-compatible patterns
- **Session Persistence**: Remember login across browser sessions
- **Logout Handling**: Secure token cleanup and session termination

**Clerk-Compatible Implementation Patterns**:
```typescript
// Authentication Hook (Clerk-compatible interface)
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoaded, setIsLoaded] = useState(false); // Clerk uses isLoaded
  const [error, setError] = useState<string | null>(null);

  // Clerk-compatible computed properties
  const isSignedIn = !!user;

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const user = await validateToken(token);
          setUser(user);
        } catch (error) {
          localStorage.removeItem('auth_token');
          setError('Session expired');
        }
      }
      setIsLoaded(true);
    };

    initAuth();
  }, []);

  const signIn = async (emailAddress: string, password: string) => {
    setError(null);
    try {
      const response = await authApi.login({ emailAddress, password });
      localStorage.setItem('auth_token', response.token);
      setUser(response.user);
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  const signOut = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return { 
    user, 
    isSignedIn, 
    isLoaded, 
    error, 
    signIn, 
    signOut 
  };
}

// User Object Shape (matches Clerk's interface)
interface User {
  id: string;
  emailAddress: string; // Clerk uses emailAddress, not email
  firstName?: string;
  lastName?: string;
  imageUrl?: string;
  username?: string;
}

// Protected Route Component (Clerk-compatible pattern)
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoaded, isSignedIn } = useAuth();

  // Loading state (matches Clerk pattern)
  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Redirect to sign-in (matches Clerk pattern)
  if (!isSignedIn) {
    return <Navigate to="/sign-in" replace />;
  }

  return <>{children}</>;
}

// Sign-in Page Component (Clerk-compatible structure)
export function SignInPage() {
  const { signIn, isLoaded } = useAuth();
  const [emailAddress, setEmailAddress] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await signIn(emailAddress, password);
      navigate('/dashboard');
    } catch (error) {
      // Error handling
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>Sign in to Admin Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="email"
              placeholder="Email address"
              value={emailAddress}
              onChange={(e) => setEmailAddress(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Button type="submit" className="w-full" disabled={!isLoaded}>
              {isLoaded ? 'Sign In' : 'Loading...'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Backend JWT Implementation**:
```python
# FastAPI backend (simple JWT for PoC)
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
from datetime import datetime, timedelta

# PoC Credentials (environment variables in production)
ADMIN_CREDENTIALS = {
    "admin@crypto-newsletter.com": {
        "password": "secure-admin-2025",
        "id": "admin-001",
        "firstName": "Admin",
        "lastName": "User"
    }
}

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    user_data = ADMIN_CREDENTIALS.get(credentials.emailAddress)
    if user_data and user_data["password"] == credentials.password:
        token = create_access_token(credentials.emailAddress)
        user = {
            "id": user_data["id"],
            "emailAddress": credentials.emailAddress,
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "username": "admin"
        }
        return {"token": token, "user": user}
    raise HTTPException(401, "Invalid credentials")

def create_access_token(email: str):
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, "your-jwt-secret", algorithm="HS256")
```

**Clerk Migration Path**:
```typescript
// Current Implementation (PoC)
import { useAuth } from '@/hooks/useAuth';

// Future Implementation (Production)
import { useAuth } from '@clerk/nextjs';

// All component code remains identical:
function Dashboard() {
  const { user, isSignedIn, signOut } = useAuth();
  
  if (!isSignedIn) return <Navigate to="/sign-in" />;
  
  return (
    <div>
      <p>Welcome, {user?.firstName}!</p>
      <Button onClick={() => signOut()}>Sign Out</Button>
    </div>
  );
}
```

**Technical Requirements**:
- JWT token validation on protected routes
- Automatic token refresh before expiration
- Secure token storage (localStorage with HTTPS)
- Error handling for expired/invalid tokens
- Logout endpoint for token invalidation

**Success Criteria**:
- Secure authentication flow with professional UX
- Zero frontend code changes required for Clerk migration
- Session persistence across browser restarts
- Proper error handling and loading states
- Complete route protection for admin areas

### 3.4 UI Component System Foundation
**Primary Responsibility**: Consistent, accessible UI components across the application

**Core UI Requirements**:
- **Design System**: Consistent colors, typography, spacing
- **Component Library**: Reusable, accessible components
- **Theme Support**: Light/dark mode capability
- **Responsive Design**: Mobile-first responsive layouts
- **Loading States**: Consistent loading and skeleton UI

**Technical Implementation**:
```typescript
// Theme Configuration
export const theme = {
  colors: {
    primary: {
      50: '#eff6ff',
      500: '#3b82f6',
      900: '#1e3a8a',
    },
    success: {
      50: '#f0fdf4',
      500: '#22c55e',
      900: '#14532d',
    },
    warning: {
      50: '#fffbeb',
      500: '#f59e0b',
      900: '#78350f',
    },
    error: {
      50: '#fef2f2',
      500: '#ef4444',
      900: '#7f1d1d',
    },
  },
  spacing: {
    xs: '0.5rem',
    sm: '1rem',
    md: '1.5rem',
    lg: '2rem',
    xl: '3rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
  },
};

// Base Layout Component
export function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar open={sidebarOpen} onOpenChange={setSidebarOpen} />
      <div className="lg:pl-64">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

**Success Criteria**:
- Consistent visual design across all pages
- Accessible components (WCAG 2.1 AA)
- Responsive layouts on all devices
- Fast component rendering (<100ms)

---

## 4. Architecture Best Practices & Integration Patterns

### 4.1 React Router Best Practices

#### Route Organization Strategy
```typescript
// Simple flat structure for MVP (4-6 routes)
<Routes>
  <Route path="/" element={<Navigate to="/dashboard" replace />} />
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/articles" element={<ArticleList />} />
  <Route path="/articles/:id" element={<ArticleDetail />} />
  <Route path="/system" element={<SystemStatus />} />
</Routes>

// Future nested structure when AI features added
<Routes>
  <Route path="/" element={<Navigate to="/dashboard" replace />} />
  <Route path="/dashboard" element={<Dashboard />} />
  
  {/* Content Management Module */}
  <Route path="/articles" element={<ArticlesLayout />}>
    <Route index element={<ArticleList />} />
    <Route path=":id" element={<ArticleDetail />} />
    <Route path="publishers" element={<PublisherManagement />} />
  </Route>
  
  {/* AI Analysis Module (Future) */}
  <Route path="/ai" element={<AILayout />}>
    <Route path="analysis" element={<SignalAnalysis />} />
    <Route path="prompts" element={<PromptEngineering />} />
    <Route path="newsletters" element={<NewsletterGeneration />} />
  </Route>
</Routes>
```

#### Navigation State Management
```typescript
// Use React Router's built-in state, not external state
const navigate = useNavigate();
const location = useLocation();
const params = useParams();

// DON'T store current route in Zustand
// DO use router hooks for navigation logic
function Sidebar() {
  const location = useLocation();
  
  return (
    <nav>
      <NavLink 
        to="/dashboard" 
        className={({ isActive }) => isActive ? 'active' : 'inactive'}
      >
        Dashboard
      </NavLink>
    </nav>
  );
}
```

### 4.2 TanStack Query Integration Patterns

#### Query Organization
```typescript
// services/api/articles.ts - API functions
export const articlesApi = {
  getArticles: (params?: ArticleParams): Promise<Article[]> =>
    apiClient.get('/api/articles', { params }),
  
  getArticle: (id: number): Promise<Article> =>
    apiClient.get(`/api/articles/${id}`),
  
  triggerIngestion: (): Promise<IngestionResult> =>
    apiClient.post('/admin/ingest'),
};

// hooks/api/useArticles.ts - Query hooks
export function useArticles(params?: ArticleParams) {
  return useQuery({
    queryKey: ['articles', params],
    queryFn: () => articlesApi.getArticles(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: ['articles', id],
    queryFn: () => articlesApi.getArticle(id),
    enabled: !!id,
  });
}

export function useIngestionTrigger() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: articlesApi.triggerIngestion,
    onSuccess: () => {
      // Invalidate articles list to refetch
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}
```

#### Query Key Conventions
```typescript
// Hierarchical query keys for efficient invalidation
const queryKeys = {
  articles: ['articles'] as const,
  articlesList: (params?: ArticleParams) => [...queryKeys.articles, 'list', params] as const,
  articleDetail: (id: number) => [...queryKeys.articles, 'detail', id] as const,
  
  system: ['system'] as const,
  systemStatus: () => [...queryKeys.system, 'status'] as const,
  systemHealth: () => [...queryKeys.system, 'health'] as const,
};

// Usage
useQuery({
  queryKey: queryKeys.articlesList(params),
  queryFn: () => articlesApi.getArticles(params),
});
```

### 4.3 Shadcn/ui + Tailwind Best Practices

#### Component Composition Strategy
```typescript
// DON'T modify shadcn/ui components directly
// DO create wrapper components for customization

// components/ui/data-table.tsx (from shadcn/ui - don't modify)
export function DataTable({ columns, data }) {
  // Shadcn/ui implementation
}

// components/common/article-table.tsx (your wrapper)
export function ArticleTable({ articles, onArticleClick }) {
  const columns = useMemo(() => [
    {
      accessorKey: 'title',
      header: 'Title',
      cell: ({ row }) => (
        <div className="max-w-sm">
          <p className="font-medium truncate">{row.getValue('title')}</p>
          <p className="text-sm text-muted-foreground">
            {row.original.publisher?.name}
          </p>
        </div>
      ),
    },
    // ... more columns
  ], []);

  return (
    <DataTable 
      columns={columns} 
      data={articles}
      onRowClick={onArticleClick}
    />
  );
}
```

#### Tailwind Organization
```typescript
// utils/cn.ts - Class name utility (from shadcn/ui)
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage in components
function Card({ className, children, ...props }) {
  return (
    <div 
      className={cn(
        "rounded-lg border bg-card text-card-foreground shadow-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
```

#### Design System Tokens
```typescript
// tailwind.config.js - Extend with project-specific tokens
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Shadcn/ui CSS variables (automatic dark mode)
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: 'hsl(var(--primary))',
        
        // Project-specific colors
        crypto: {
          bitcoin: '#f7931a',
          ethereum: '#627eea',
          success: '#10b981',
          warning: '#f59e0b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

### 4.4 Zustand State Management Patterns

#### Store Organization
```typescript
// stores/auth.ts - Authentication state
interface AuthState {
  user: User | null;
  token: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('admin_token'),
  
  login: async (credentials) => {
    const response = await authApi.login(credentials);
    localStorage.setItem('admin_token', response.token);
    set({ user: response.user, token: response.token });
  },
  
  logout: () => {
    localStorage.removeItem('admin_token');
    set({ user: null, token: null });
  },
  
  checkAuth: async () => {
    const token = get().token;
    if (token) {
      try {
        const user = await authApi.validateToken(token);
        set({ user });
      } catch {
        get().logout();
      }
    }
  },
}));

// stores/ui.ts - UI state only
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  theme: 'light',
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => set({ theme }),
}));
```

#### State vs Server Data Separation
```typescript
// GOOD - Clear separation
function ArticleList() {
  // Server state - use TanStack Query
  const { data: articles, isLoading } = useArticles();
  
  // UI state - use Zustand
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  
  // Local component state - use useState
  const [selectedArticles, setSelectedArticles] = useState<number[]>([]);
  
  return (
    <div>
      {/* Component implementation */}
    </div>
  );
}

// BAD - Mixing server data in Zustand
const useStore = create((set) => ({
  articles: [], // DON'T - use TanStack Query instead
  sidebarOpen: false, // OK - UI state
}));
```

### 4.5 Integration Anti-Patterns to Avoid

#### Common Mistakes
```typescript
// ❌ DON'T store server data in Zustand
const useStore = create((set) => ({
  articles: [],
  setArticles: (articles) => set({ articles }),
}));

// ✅ DO use TanStack Query for server data
const { data: articles } = useArticles();

// ❌ DON'T put routing state in external stores
const useStore = create((set) => ({
  currentRoute: '/dashboard',
  setRoute: (route) => set({ currentRoute: route }),
}));

// ✅ DO use React Router hooks
const location = useLocation();
const navigate = useNavigate();

// ❌ DON'T modify shadcn/ui components directly
// components/ui/button.tsx
export function Button({ className, ...props }) {
  return (
    <button 
      className="bg-red-500 text-white" // DON'T hardcode colors
      {...props} 
    />
  );
}

// ✅ DO create wrapper components
// components/common/action-button.tsx
export function ActionButton({ variant = "default", ...props }) {
  return (
    <Button 
      className={cn(
        variant === "danger" && "bg-red-500 hover:bg-red-600"
      )}
      {...props} 
    />
  );
}
```

---

## 5. Development Configuration

### 5.1 Package.json Configuration
```json
{
  "name": "crypto-newsletter-admin",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,md}\"",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:ui": "vitest --ui"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.4.0",
    "react-hook-form": "^7.45.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0",
    "lucide-react": "^0.280.0",
    "date-fns": "^2.30.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^1.14.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.2",
    "vite": "^5.0.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "tailwindcss-animate": "^1.0.0"
  }
}
```

### 5.2 Vite Configuration
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Proxy API calls to FastAPI backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor libraries for better caching
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          ui: ['lucide-react', 'date-fns'],
        },
      },
    },
  },
});
```

### 5.3 TanStack Query Configuration
```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Background refetch for fresh data
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (error instanceof Error && error.message.includes('4')) {
          return false;
        }
        return failureCount < 3;
      },
    },
    mutations: {
      retry: 1,
    },
  },
});

// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        {/* Your app */}
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### 5.4 Shadcn/ui Configuration
```json
// components.json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/styles/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

```css
/* src/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --border: 214.3 31.8% 91.4%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode variables */
  }
}
```

### 4.3 TypeScript Configuration
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 5.5 Authentication Configuration
```bash
# .env.example
VITE_API_URL=https://bitcoin-newsletter-api.onrender.com
VITE_WS_URL=wss://bitcoin-newsletter-api.onrender.com
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=development

# Authentication (PoC)
VITE_AUTH_PROVIDER=jwt  # Will be 'clerk' in production

# .env.local (for development)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_VERSION=1.0.0-dev
VITE_APP_ENV=development
VITE_AUTH_PROVIDER=jwt
```

```typescript
// src/lib/auth.ts - Environment-aware auth configuration
export const authConfig = {
  provider: import.meta.env.VITE_AUTH_PROVIDER || 'jwt',
  apiUrl: import.meta.env.VITE_API_URL,
  
  // PoC credentials (development only)
  defaultCredentials: {
    emailAddress: 'admin@crypto-newsletter.com',
    password: 'secure-admin-2025'
  },
  
  // Clerk configuration (future)
  clerk: {
    publishableKey: import.meta.env.VITE_CLERK_PUBLISHABLE_KEY,
  }
};

// Type definitions for auth providers
export type AuthProvider = 'jwt' | 'clerk';

export interface AuthConfig {
  provider: AuthProvider;
  apiUrl: string;
  defaultCredentials?: {
    emailAddress: string;
    password: string;
  };
  clerk?: {
    publishableKey: string;
  };
}
```

---

## 6. Quality Standards

### 6.1 Code Quality Requirements
- **TypeScript Strict Mode**: All code must pass strict type checking
- **ESLint Rules**: Zero linting errors in production builds
- **Test Coverage**: >80% unit test coverage for utility functions
- **Bundle Size**: <500KB initial bundle size
- **Performance**: Lighthouse score >90 for performance

### 6.2 Browser Compatibility
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile Support**: iOS Safari 14+, Chrome Mobile 90+
- **JavaScript**: ES2020 features supported
- **CSS**: CSS Grid and Flexbox layouts

### 6.3 Accessibility Requirements
- **WCAG 2.1 AA**: Full compliance for all interactive elements
- **Keyboard Navigation**: Complete keyboard accessibility
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Color Contrast**: 4.5:1 minimum contrast ratio

---

## 7. Deployment Architecture

### 7.1 Render Configuration
```yaml
# render.yaml
services:
  - type: web
    name: crypto-newsletter-admin
    env: node
    plan: starter
    buildCommand: npm ci && npm run build
    startCommand: npm run preview
    envVars:
      - key: NODE_ENV
        value: production
      - key: VITE_API_URL
        value: https://bitcoin-newsletter-api.onrender.com
      - key: VITE_WS_URL
        value: wss://bitcoin-newsletter-api.onrender.com
      - key: VITE_APP_VERSION
        sync: false
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

### 7.2 Build Optimization
- **Code Splitting**: Automatic route-based code splitting
- **Asset Optimization**: Image compression and lazy loading
- **Bundle Analysis**: Webpack bundle analyzer integration
- **Caching Strategy**: Aggressive caching for static assets

---

## 8. Success Metrics

### 8.1 Development Productivity
- **Setup Time**: New developer productive in <15 minutes
- **Build Performance**: Development builds in <2 seconds
- **Hot Reload**: Changes visible in <200ms
- **Type Safety**: 100% TypeScript coverage

### 8.2 Application Performance
- **Initial Load**: <3 seconds on 3G connection
- **Route Navigation**: <200ms route transitions
- **API Response**: <1 second for cached responses
- **Memory Usage**: <50MB baseline memory consumption

### 8.3 Code Quality
- **Test Coverage**: >80% for utility functions
- **Bundle Size**: <500KB initial bundle
- **Lighthouse Score**: >90 for performance, accessibility, SEO
- **Zero Runtime Errors**: No uncaught exceptions in production

---

## 9. Implementation Timeline

### Week 1: Project Setup & Core Infrastructure
- **Day 1**: Project initialization with Vite + React + TypeScript
- **Day 2**: Shadcn/ui setup and basic component library
- **Day 3**: API client implementation and authentication foundation
- **Day 4**: Routing setup and protected route implementation
- **Day 5**: Basic layout components and navigation structure

### Week 2: Development Environment Optimization
- **Day 6-7**: ESLint, Prettier, and code quality tools setup
- **Day 8-9**: Testing framework and initial test coverage
- **Day 10**: Environment configuration and deployment preparation

---

## 10. Next Steps & Integration Points

### Immediate Follow-up PRDs (Priority Order)
1. **User Authentication & Authorization PRD** - Complete the auth flow
2. **Overview Dashboard PRD** - Main dashboard implementation
3. **Content Management PRD** - Article and publisher management
4. **System Monitoring PRD** - Real-time system health monitoring

### Integration Requirements
- **Backend API**: CORS configuration for admin dashboard domain
- **Authentication**: JWT token validation endpoints
- **WebSocket**: Real-time updates capability (future enhancement)

---

## 11. Risk Assessment

### Technical Risks
- **API Integration Complexity**: Mitigation through comprehensive API client testing
- **Authentication Security**: Mitigation through secure token handling and HTTPS enforcement
- **Performance on Mobile**: Mitigation through responsive design testing and optimization

### Development Risks
- **Dependency Management**: Mitigation through lockfile usage and regular updates
- **Build Complexity**: Mitigation through simple, well-documented build pipeline
- **Team Onboarding**: Mitigation through comprehensive documentation and setup automation

---

*Document Version: 1.0*
*Last Updated: August 13, 2025*
*Status: Ready for Implementation*
*Priority: CRITICAL - Foundation for all other back office PRDs*
*Implementation Time: 2 weeks*