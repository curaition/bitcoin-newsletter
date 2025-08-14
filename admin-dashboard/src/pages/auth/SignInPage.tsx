/**
 * Sign In Page
 * 
 * Authentication page with email/password form and error handling.
 * Redirects to dashboard on successful authentication.
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSignIn } from '@/hooks/auth/useAuth';

export function SignInPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, isLoading, error, clearError } = useSignIn();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Get redirect location from state (set by ProtectedRoute)
  const from = (location.state as any)?.from || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!email || !password) {
      return;
    }

    try {
      await signIn({ emailAddress: email, password });
      navigate(from, { replace: true });
    } catch (err) {
      // Error is handled by useSignIn hook
      console.error('Sign in failed:', err);
    }
  };

  // Debug: Log component render (development only)
  if (import.meta.env.DEV) {
    console.log('SignInPage rendering, error:', error, 'isLoading:', isLoading);
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', backgroundColor: '#ffffff' }}>
      <div style={{ width: '100%', maxWidth: '400px' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>Bitcoin Newsletter</h1>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Sign in to access the admin dashboard
          </p>
          <span style={{
            display: 'inline-block',
            padding: '0.25rem 0.75rem',
            border: '1px solid #ccc',
            borderRadius: '0.375rem',
            fontSize: '0.875rem'
          }}>
            Administrator Access
          </span>
        </div>

        {/* Sign in form */}
        <div style={{
          border: '1px solid #ccc',
          borderRadius: '0.5rem',
          padding: '2rem',
          backgroundColor: '#ffffff',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>Sign In</h2>
          <p style={{ color: '#666', marginBottom: '1.5rem' }}>
            Enter your credentials to access the dashboard
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Error display */}
            {error && (
              <div style={{
                padding: '0.75rem',
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '0.375rem',
                color: '#dc2626'
              }}>
                {error.message || 'Authentication failed. Please try again.'}
              </div>
            )}

            {/* Email field */}
            <div>
              <label htmlFor="email" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ccc',
                  borderRadius: '0.375rem',
                  fontSize: '1rem'
                }}
              />
            </div>

            {/* Password field */}
            <div>
              <label htmlFor="password" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
                Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ccc',
                  borderRadius: '0.375rem',
                  fontSize: '1rem'
                }}
              />
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading || !email || !password}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: isLoading || !email || !password ? '#ccc' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: isLoading || !email || !password ? 'not-allowed' : 'pointer'
              }}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        {/* Development note */}
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '0.875rem', color: '#666' }}>
            Development environment - Mock authentication enabled
          </p>
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            Use any email/password combination to sign in
          </p>
        </div>
      </div>
    </div>
  );
}
