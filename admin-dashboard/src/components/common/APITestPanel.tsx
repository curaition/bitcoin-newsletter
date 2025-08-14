/**
 * API Test Panel
 * 
 * Component to test and demonstrate API integration functionality
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { useAuth, useSignIn } from '@/hooks/auth/useAuth';
import { useSystemStatus, useHealthCheck, useConnectionTest } from '@/hooks/api/useSystem';
import { useArticles } from '@/hooks/api/useArticles';
import { Loader2, CheckCircle, XCircle, Wifi, Database, Server } from 'lucide-react';

export function APITestPanel() {
  const [testEmail, setTestEmail] = useState('admin@example.com');
  const [testPassword, setTestPassword] = useState('password123');
  
  // Auth hooks
  const { user, isSignedIn, isLoaded, signOut } = useAuth();
  const { signIn, isLoading: isSigningIn, error: signInError } = useSignIn();
  
  // API hooks
  const connectionTest = useConnectionTest();
  const healthCheck = useHealthCheck({ enabled: isSignedIn });
  const systemStatus = useSystemStatus({ enabled: isSignedIn });
  const articles = useArticles({ 
    limit: 5, 
    enabled: isSignedIn 
  });

  // Test authentication
  const handleTestSignIn = async () => {
    try {
      await signIn({
        emailAddress: testEmail,
        password: testPassword,
      });
    } catch (error) {
      console.error('Sign in failed:', error);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out failed:', error);
    }
  };

  // Test connection
  const handleTestConnection = () => {
    connectionTest.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Authentication Test */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Authentication Test
          </CardTitle>
          <CardDescription>
            Test JWT authentication with the backend
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isLoaded ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading auth state...</span>
            </div>
          ) : isSignedIn ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="success">Signed In</Badge>
                <span className="text-sm">Welcome, {user?.emailAddress}</span>
              </div>
              <Button onClick={handleSignOut} variant="outline" size="sm">
                Sign Out
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <Input
                  placeholder="Email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={testPassword}
                  onChange={(e) => setTestPassword(e.target.value)}
                />
              </div>
              {signInError && (
                <div className="text-sm text-red-600">
                  Error: {signInError.message}
                </div>
              )}
              <Button 
                onClick={handleTestSignIn} 
                disabled={isSigningIn}
                size="sm"
              >
                {isSigningIn && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                Test Sign In
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Connection Test */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wifi className="h-5 w-5" />
            Connection Test
          </CardTitle>
          <CardDescription>
            Test basic connectivity to the backend API
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Button 
              onClick={handleTestConnection}
              disabled={connectionTest.isPending}
              size="sm"
            >
              {connectionTest.isPending && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Test Connection
            </Button>
            
            {connectionTest.data !== undefined && (
              <Badge variant={connectionTest.data ? "success" : "destructive"}>
                {connectionTest.data ? "Connected" : "Failed"}
              </Badge>
            )}
          </div>
          
          {connectionTest.error && (
            <div className="text-sm text-red-600">
              Connection failed: {connectionTest.error.message}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Health Check */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Health Check
          </CardTitle>
          <CardDescription>
            Backend health status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {healthCheck.isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Checking health...</span>
            </div>
          ) : healthCheck.error ? (
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <span className="text-red-600">Health check failed</span>
            </div>
          ) : healthCheck.data ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <Badge variant={healthCheck.data.isHealthy ? "success" : "destructive"}>
                  {healthCheck.data.status}
                </Badge>
              </div>
              <div className="text-sm text-muted-foreground">
                Last checked: {healthCheck.data.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* System Status */}
      {isSignedIn && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              System Status
            </CardTitle>
            <CardDescription>
              Detailed system component status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {systemStatus.isLoading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading system status...</span>
              </div>
            ) : systemStatus.error ? (
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-500" />
                <span className="text-red-600">Failed to load system status</span>
              </div>
            ) : systemStatus.data ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant={
                    systemStatus.data.overallHealth === 'healthy' ? 'success' :
                    systemStatus.data.overallHealth === 'warning' ? 'warning' : 'destructive'
                  }>
                    {systemStatus.data.overallHealth}
                  </Badge>
                  <span className="text-sm">Overall Health</span>
                </div>
                
                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${
                      systemStatus.data.api?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    API
                  </div>
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${
                      systemStatus.data.database?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    Database
                  </div>
                  <div className="flex items-center gap-1">
                    <div className={`w-2 h-2 rounded-full ${
                      systemStatus.data.celery?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    Celery
                  </div>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Articles Test */}
      {isSignedIn && (
        <Card>
          <CardHeader>
            <CardTitle>Articles API Test</CardTitle>
            <CardDescription>
              Test article fetching with shared types
            </CardDescription>
          </CardHeader>
          <CardContent>
            {articles.isLoading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading articles...</span>
              </div>
            ) : articles.error ? (
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-500" />
                <span className="text-red-600">Failed to load articles</span>
              </div>
            ) : articles.data ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Loaded {articles.data.articles.length} articles</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  Total: {articles.data.pagination.total} articles
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
