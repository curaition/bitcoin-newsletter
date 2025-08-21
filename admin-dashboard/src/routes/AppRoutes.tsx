/**
 * Application Routes Configuration
 *
 * Defines all routes with authentication protection and layout structure.
 * Uses React Router v6 with nested routes and protected route components.
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute, PublicRoute } from '@/components/layout/ProtectedRoute';
import { AppLayout } from '@/components/layout/AppLayout';

// Page components
import { SignInPage } from '@/pages/auth/SignInPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { ArticlesPage } from '@/pages/articles/ArticlesPage';
import { ArticleDetailPage } from '@/pages/articles/ArticleDetailPage';
import { NewslettersPage } from '@/pages/newsletters/NewslettersPage';
import { NewsletterDetailPage } from '@/pages/newsletters/NewsletterDetailPage';
import { NewsletterGeneratePage } from '@/pages/newsletters/NewsletterGeneratePage';
import { SystemPage } from '@/pages/system/SystemPage';

// Error boundary component
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

export function AppRoutes() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public routes (authentication) */}
        <Route
          path="/auth/sign-in"
          element={
            <PublicRoute>
              <SignInPage />
            </PublicRoute>
          }
        />

        {/* Protected routes (main application) */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* Nested protected routes */}
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="articles" element={<ArticlesPage />} />
          <Route path="articles/:id" element={<ArticleDetailPage />} />
          <Route path="newsletters" element={<NewslettersPage />} />
          <Route path="newsletters/:id" element={<NewsletterDetailPage />} />
          <Route path="newsletters/generate" element={<NewsletterGeneratePage />} />
          <Route path="system" element={<SystemPage />} />

          {/* Catch-all redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>

        {/* Root redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </ErrorBoundary>
  );
}
