/**
 * TanStack Query Configuration
 *
 * Centralized query client setup with error handling and authentication integration
 */

import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';
import { APIError } from '../../../../shared/utils/api-helpers';
import { authService } from '@/services/auth/auth-service';

// ============================================================================
// Error Handling
// ============================================================================

function handleQueryError(error: unknown): void {
  console.error('Query error:', error);

  // Handle authentication errors
  if (error instanceof APIError) {
    if (error.status === 401) {
      // Token expired or invalid - sign out user
      authService.signOut();
      return;
    }

    if (error.status === 403) {
      console.warn('Access forbidden:', error.message);
      return;
    }

    if (error.status >= 500) {
      console.error('Server error:', error.message);
      return;
    }
  }
}

function handleMutationError(error: unknown): void {
  console.error('Mutation error:', error);

  // Handle authentication errors for mutations
  if (error instanceof APIError && error.status === 401) {
    authService.signOut();
  }
}

// ============================================================================
// Query Client Configuration
// ============================================================================

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleQueryError,
  }),

  mutationCache: new MutationCache({
    onError: handleMutationError,
  }),

  defaultOptions: {
    queries: {
      // Stale time - how long data is considered fresh
      staleTime: 5 * 60 * 1000, // 5 minutes

      // Cache time - how long data stays in cache after component unmounts
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)

      // Retry configuration
      retry: (failureCount, error) => {
        // Don't retry on authentication errors
        if (error instanceof APIError && [401, 403].includes(error.status)) {
          return false;
        }

        // Don't retry on client errors (4xx)
        if (error instanceof APIError && error.status >= 400 && error.status < 500) {
          return false;
        }

        // Retry up to 3 times for server errors
        return failureCount < 3;
      },

      // Retry delay with exponential backoff
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Refetch on window focus (disabled for admin dashboard)
      refetchOnWindowFocus: false,

      // Refetch on reconnect
      refetchOnReconnect: true,

      // Background refetch interval (disabled by default)
      refetchInterval: false,
    },

    mutations: {
      // Retry mutations once on network errors
      retry: (failureCount, error) => {
        if (error instanceof APIError && error.status >= 400) {
          return false; // Don't retry client or server errors
        }
        return failureCount < 1; // Retry once for network errors
      },

      // Mutation retry delay
      retryDelay: 1000,
    },
  },
});

// ============================================================================
// Query Keys Factory
// ============================================================================

export const queryKeys = {
  // Authentication
  auth: ['auth'] as const,
  user: () => [...queryKeys.auth, 'user'] as const,

  // Articles
  articles: ['articles'] as const,
  articleList: (params?: Record<string, any>) =>
    [...queryKeys.articles, 'list', params] as const,
  article: (id: number) =>
    [...queryKeys.articles, 'detail', id] as const,

  // Publishers
  publishers: () => ['publishers'] as const,

  // Newsletters
  newsletters: ['newsletters'] as const,
  newsletterList: (params?: Record<string, any>) =>
    [...queryKeys.newsletters, 'list', params] as const,
  newsletter: (id: number) =>
    [...queryKeys.newsletters, 'detail', id] as const,
  newsletterStats: () => [...queryKeys.newsletters, 'stats'] as const,
  newsletterHealth: () => [...queryKeys.newsletters, 'health'] as const,
  newsletterSearch: (params?: Record<string, any>) =>
    [...queryKeys.newsletters, 'search', params] as const,
  newsletterAnalytics: (period: string) =>
    [...queryKeys.newsletters, 'analytics', period] as const,

  // System
  system: ['system'] as const,
  systemStatus: () => [...queryKeys.system, 'status'] as const,
  healthCheck: () => [...queryKeys.system, 'health'] as const,

  // Admin
  admin: ['admin'] as const,
  adminTasks: () => [...queryKeys.admin, 'tasks'] as const,
  adminTask: (taskId: string) =>
    [...queryKeys.admin, 'task', taskId] as const,
} as const;

// ============================================================================
// Query Invalidation Helpers
// ============================================================================

export const queryInvalidation = {
  // Invalidate all queries
  all: () => queryClient.invalidateQueries(),

  // Authentication
  auth: () => queryClient.invalidateQueries({ queryKey: queryKeys.auth }),

  // Articles
  articles: () => queryClient.invalidateQueries({ queryKey: queryKeys.articles }),
  articleList: () => queryClient.invalidateQueries({
    queryKey: queryKeys.articles,
    predicate: (query) => query.queryKey[1] === 'list'
  }),

  // Newsletters
  newsletters: () => queryClient.invalidateQueries({ queryKey: queryKeys.newsletters }),
  newsletterList: () => queryClient.invalidateQueries({
    queryKey: queryKeys.newsletters,
    predicate: (query) => query.queryKey[1] === 'list'
  }),
  newsletterStats: () => queryClient.invalidateQueries({
    queryKey: queryKeys.newsletters,
    predicate: (query) => query.queryKey[1] === 'stats'
  }),

  // System
  system: () => queryClient.invalidateQueries({ queryKey: queryKeys.system }),

  // Admin
  admin: () => queryClient.invalidateQueries({ queryKey: queryKeys.admin }),
};

// ============================================================================
// Prefetch Helpers
// ============================================================================

export const queryPrefetch = {
  systemStatus: () => queryClient.prefetchQuery({
    queryKey: queryKeys.systemStatus(),
    queryFn: async () => {
      const { apiClient } = await import('@/services/api/client');
      return apiClient.getSystemStatus();
    },
    staleTime: 30 * 1000, // 30 seconds
  }),

  healthCheck: () => queryClient.prefetchQuery({
    queryKey: queryKeys.healthCheck(),
    queryFn: async () => {
      const { apiClient } = await import('@/services/api/client');
      return apiClient.getHealthCheck();
    },
    staleTime: 60 * 1000, // 1 minute
  }),
};

// ============================================================================
// Development Tools
// ============================================================================

if (import.meta.env.DEV) {
  // Log query cache changes in development
  queryClient.getQueryCache().subscribe((event) => {
    if (event.type === 'added') {
      console.log('Query added:', event.query.queryKey);
    }
    if (event.type === 'removed') {
      console.log('Query removed:', event.query.queryKey);
    }
  });
}
