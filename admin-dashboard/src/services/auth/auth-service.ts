/**
 * Authentication Service
 * 
 * Clerk-compatible authentication patterns for easy future migration
 */

import type { User, LoginRequest, LoginResponse } from '../../../../shared/types/api';
import { apiClient, setAuthToken, getAuthToken } from '../api/client';
import { isValidEmail } from '../../../../shared/utils/api-helpers';
import { authConfig } from '../../utils/env';

export interface AuthState {
  user: User | null;
  isLoaded: boolean;
  isSignedIn: boolean;
}

export interface SignInParams {
  emailAddress: string;
  password: string;
}

// interface AuthErrorInterface {
//   code: string;
//   message: string;
// }

class AuthService {
  private listeners: Set<(state: AuthState) => void> = new Set();
  private state: AuthState = {
    user: null,
    isLoaded: false,
    isSignedIn: false,
  };

  constructor() {
    this.initialize();
  }

  // ============================================================================
  // Initialization
  // ============================================================================

  private async initialize(): Promise<void> {
    try {
      const token = getAuthToken();
      if (token) {
        // In development with mock auth, accept any token
        if (import.meta.env.DEV && token.startsWith('mock-jwt-token-')) {
          await this.validateMockToken(token);
        } else {
          // Validate token by trying to refresh it
          await this.validateToken();
        }
      }
    } catch (error) {
      console.warn('Token validation failed:', error);
      this.signOut();
    } finally {
      this.updateState({ isLoaded: true });
    }
  }

  private async validateMockToken(_token: string): Promise<void> {
    // Mock token validation - always succeeds in development
    const mockUser: User = {
      id: 'mock-user-123',
      emailAddress: 'admin@example.com',
      firstName: 'Admin',
      lastName: 'User',
      imageUrl: undefined,
      username: 'admin',
    };

    this.updateState({
      user: mockUser,
      isSignedIn: true,
    });

    console.log('🎭 Mock token validated:', mockUser);
  }

  private async validateToken(): Promise<void> {
    try {
      const response = await apiClient.refreshToken();
      this.updateState({
        user: response.user,
        isSignedIn: true,
      });
      setAuthToken(response.token);
    } catch (error) {
      throw new Error('Token validation failed');
    }
  }

  // ============================================================================
  // State Management
  // ============================================================================

  private updateState(updates: Partial<AuthState>): void {
    this.state = { ...this.state, ...updates };
    this.notifyListeners();
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  public subscribe(listener: (state: AuthState) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  public getState(): AuthState {
    return this.state;
  }

  // ============================================================================
  // Authentication Methods (Clerk-compatible)
  // ============================================================================

  async signIn({ emailAddress, password }: SignInParams): Promise<User> {
    // Validation
    if (!emailAddress || !password) {
      throw new AuthError('missing_credentials', 'Email and password are required');
    }

    if (!isValidEmail(emailAddress)) {
      throw new AuthError('invalid_email', 'Please enter a valid email address');
    }

    // Mock authentication for development and production demo
    if (authConfig.enableMockAuth) {
      // Only allow specific client credentials in production
      if (!import.meta.env.DEV &&
          (emailAddress !== authConfig.clientEmail || password !== authConfig.clientPassword)) {
        throw new AuthError('invalid_credentials', 'Invalid email or password');
      }
      return this.mockSignIn(emailAddress, password);
    }

    if (password.length < 6) {
      throw new AuthError('weak_password', 'Password must be at least 6 characters');
    }

    try {
      const credentials: LoginRequest = { emailAddress, password };
      const response: LoginResponse = await apiClient.login(credentials);

      // Update auth state
      this.updateState({
        user: response.user,
        isSignedIn: true,
      });

      // Store token
      setAuthToken(response.token);

      return response.user;
    } catch (error: any) {
      // Map API errors to Clerk-compatible format
      const authError = this.mapApiError(error);
      throw authError;
    }
  }

  private async mockSignIn(emailAddress: string, _password: string): Promise<User> {
    // Simulate API delay for realistic UX
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Accept any valid email/password combination
    const mockUser: User = {
      id: 'mock-user-123',
      emailAddress,
      firstName: 'Admin',
      lastName: 'User',
      imageUrl: undefined,
      username: 'admin',
    };

    // Generate mock token
    const mockToken = `mock-jwt-token-${Date.now()}`;

    // Update auth state
    this.updateState({
      user: mockUser,
      isSignedIn: true,
    });

    // Store mock token
    setAuthToken(mockToken);

    console.log('🎭 Mock authentication successful:', mockUser);

    return mockUser;
  }

  async signOut(): Promise<void> {
    try {
      // Attempt to notify backend
      if (this.state.isSignedIn) {
        await apiClient.logout();
      }
    } catch (error) {
      // Continue with local signout even if backend call fails
      console.warn('Backend logout failed:', error);
    } finally {
      // Clear local state
      this.updateState({
        user: null,
        isSignedIn: false,
      });

      // Clear token
      setAuthToken(null);
    }
  }

  async refreshSession(): Promise<User | null> {
    if (!this.state.isSignedIn) {
      return null;
    }

    try {
      const response = await apiClient.refreshToken();
      
      this.updateState({
        user: response.user,
        isSignedIn: true,
      });

      setAuthToken(response.token);
      return response.user;
    } catch (error) {
      // Token refresh failed, sign out
      await this.signOut();
      throw error;
    }
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  private mapApiError(error: any): AuthError {
    // Map common API errors to Clerk-compatible error codes
    const errorMap: Record<string, { code: string; message: string }> = {
      'invalid_credentials': {
        code: 'form_identifier_not_found',
        message: 'Invalid email or password',
      },
      'user_not_found': {
        code: 'form_identifier_not_found',
        message: 'No account found with this email address',
      },
      'invalid_password': {
        code: 'form_password_incorrect',
        message: 'Incorrect password',
      },
      'account_locked': {
        code: 'form_identifier_exists',
        message: 'Account is temporarily locked',
      },
    };

    const mapped = errorMap[error.code] || {
      code: 'form_unknown_error',
      message: error.message || 'An unexpected error occurred',
    };

    return new AuthError(mapped.code, mapped.message);
  }

  // Clerk-compatible getters
  get user(): User | null {
    return this.state.user;
  }

  get isLoaded(): boolean {
    return this.state.isLoaded;
  }

  get isSignedIn(): boolean {
    return this.state.isSignedIn;
  }
}

// ============================================================================
// Auth Error Class
// ============================================================================

class AuthError extends Error {
  public code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = 'AuthError';
    this.code = code;
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

export const authService = new AuthService();

// Export for testing
export { AuthError };
