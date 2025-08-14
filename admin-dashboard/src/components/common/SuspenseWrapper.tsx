/**
 * Suspense Wrapper Component
 * 
 * Provides loading states for lazy-loaded components and routes.
 * Handles errors gracefully with fallback UI.
 */

import { Suspense, ReactNode } from 'react';
import { PageLoading } from './LoadingSpinner';
import { ErrorBoundary } from './ErrorBoundary';

interface SuspenseWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
  errorFallback?: ReactNode;
}

export function SuspenseWrapper({ 
  children, 
  fallback,
  errorFallback 
}: SuspenseWrapperProps) {
  return (
    <ErrorBoundary fallback={errorFallback}>
      <Suspense fallback={fallback || <PageLoading />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}

// ============================================================================
// Route Suspense Wrapper
// ============================================================================

interface RouteSuspenseProps {
  children: ReactNode;
}

export function RouteSuspense({ children }: RouteSuspenseProps) {
  return (
    <SuspenseWrapper 
      fallback={<PageLoading message="Loading page..." />}
    >
      {children}
    </SuspenseWrapper>
  );
}
