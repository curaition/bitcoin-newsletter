/**
 * Protected Route Component
 * 
 * Handles authentication-based route protection with loading states
 * and automatic redirects for unauthenticated users.
 */

import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/auth/useAuth';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: ReactNode;
  redirectTo?: string;
  fallback?: ReactNode;
}

export function ProtectedRoute({ 
  children, 
  redirectTo = '/auth/sign-in',
  fallback 
}: ProtectedRouteProps) {
  const { user, isLoaded, isSignedIn } = useAuth();
  const location = useLocation();

  // Show loading state while auth is being determined
  if (!isLoaded) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center p-8 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold">Loading...</h3>
              <p className="text-sm text-muted-foreground">
                Checking authentication status
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Redirect to sign-in if not authenticated
  if (!isSignedIn || !user) {
    return (
      <Navigate 
        to={redirectTo} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Render protected content
  return <>{children}</>;
}

// ============================================================================
// Public Route Component (for auth pages)
// ============================================================================

interface PublicRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

export function PublicRoute({ 
  children, 
  redirectTo = '/dashboard' 
}: PublicRouteProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const location = useLocation();

  // Show loading state while auth is being determined
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center p-8 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold">Loading...</h3>
              <p className="text-sm text-muted-foreground">
                Checking authentication status
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Redirect to dashboard if already authenticated
  if (isSignedIn) {
    // Check if there's a redirect location from the protected route
    const from = (location.state as any)?.from || redirectTo;
    return <Navigate to={from} replace />;
  }

  // Render public content (sign-in page)
  return <>{children}</>;
}
