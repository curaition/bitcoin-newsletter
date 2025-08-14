/**
 * Authentication Hooks
 * 
 * Clerk-compatible React hooks for authentication state management
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { User } from '../../../../shared/types/api';
import { authService, type AuthState, type SignInParams, AuthError } from '@/services/auth/auth-service';

// Safe navigation hook that doesn't throw if router is not available
function useSafeNavigate() {
  try {
    return useNavigate();
  } catch {
    // Return a no-op function if router is not available
    return () => {};
  }
}

// ============================================================================
// Main Authentication Hook
// ============================================================================

export interface UseAuthOptions {
  redirectTo?: string;
  or?: 'redirect' | 'throw';
}

export interface UseAuthReturn {
  // State
  user: User | null;
  isLoaded: boolean;
  isSignedIn: boolean;
  
  // Actions
  signIn: (params: SignInParams) => Promise<User>;
  signOut: () => Promise<void>;
  refresh: () => Promise<User | null>;
  
  // Loading states
  isSigningIn: boolean;
  isSigningOut: boolean;
}

export function useAuth(options: UseAuthOptions = {}): UseAuthReturn {
  const navigate = useSafeNavigate();
  const [authState, setAuthState] = useState<AuthState>(authService.getState());
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);

  // Subscribe to auth state changes
  useEffect(() => {
    const unsubscribe = authService.subscribe(setAuthState);
    return unsubscribe;
  }, []);

  // Handle redirect logic
  useEffect(() => {
    if (authState.isLoaded && !authState.isSignedIn && options.or === 'redirect') {
      const redirectTo = options.redirectTo || '/auth/sign-in';
      navigate(redirectTo, { replace: true });
    }
  }, [authState.isLoaded, authState.isSignedIn, options.or, options.redirectTo, navigate]);

  // Sign in handler
  const signIn = useCallback(async (params: SignInParams): Promise<User> => {
    setIsSigningIn(true);
    try {
      const user = await authService.signIn(params);
      return user;
    } finally {
      setIsSigningIn(false);
    }
  }, []);

  // Sign out handler
  const signOut = useCallback(async (): Promise<void> => {
    setIsSigningOut(true);
    try {
      await authService.signOut();
    } finally {
      setIsSigningOut(false);
    }
  }, []);

  // Refresh session handler
  const refresh = useCallback(async (): Promise<User | null> => {
    return authService.refreshSession();
  }, []);

  return {
    // State
    user: authState.user,
    isLoaded: authState.isLoaded,
    isSignedIn: authState.isSignedIn,
    
    // Actions
    signIn,
    signOut,
    refresh,
    
    // Loading states
    isSigningIn,
    isSigningOut,
  };
}

// ============================================================================
// User Hook (Clerk-compatible)
// ============================================================================

export function useUser(options: UseAuthOptions = {}): {
  user: User | null;
  isLoaded: boolean;
  isSignedIn: boolean;
} {
  const { user, isLoaded, isSignedIn } = useAuth(options);
  
  return {
    user,
    isLoaded,
    isSignedIn,
  };
}

// ============================================================================
// Sign In Hook
// ============================================================================

export interface UseSignInReturn {
  signIn: (params: SignInParams) => Promise<User>;
  isLoading: boolean;
  error: AuthError | null;
  clearError: () => void;
}

export function useSignIn(): UseSignInReturn {
  const { signIn } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AuthError | null>(null);

  const handleSignIn = useCallback(async (params: SignInParams): Promise<User> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const user = await signIn(params);
      return user;
    } catch (err) {
      const authError = err instanceof AuthError ? err : new AuthError('unknown_error', 'An unexpected error occurred');
      setError(authError);
      throw authError;
    } finally {
      setIsLoading(false);
    }
  }, [signIn]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    signIn: handleSignIn,
    isLoading,
    error,
    clearError,
  };
}

// ============================================================================
// Sign Out Hook
// ============================================================================

export interface UseSignOutReturn {
  signOut: () => Promise<void>;
  isLoading: boolean;
}

export function useSignOut(): UseSignOutReturn {
  const { signOut } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleSignOut = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      await signOut();
    } finally {
      setIsLoading(false);
    }
  }, [signOut]);

  return {
    signOut: handleSignOut,
    isLoading,
  };
}

// ============================================================================
// Session Hook
// ============================================================================

export interface UseSessionReturn {
  session: { user: User } | null;
  isLoaded: boolean;
  refresh: () => Promise<User | null>;
}

export function useSession(): UseSessionReturn {
  const { user, isLoaded, refresh } = useAuth();

  return {
    session: user ? { user } : null,
    isLoaded,
    refresh,
  };
}
