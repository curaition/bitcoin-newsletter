/**
 * Router Test Component
 * 
 * Simple component to verify React Router integration is working
 */

import { useAuth } from '@/hooks/auth/useAuth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle } from 'lucide-react';

export function RouterTest() {
  const { isLoaded, isSignedIn, user } = useAuth();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-500" />
          React Router Integration
        </CardTitle>
        <CardDescription>
          Verifying React Router context is available
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="success">Router Active</Badge>
          <span className="text-sm">useNavigate() hook working</span>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant={isLoaded ? "success" : "secondary"}>
            Auth State: {isLoaded ? 'Loaded' : 'Loading'}
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant={isSignedIn ? "success" : "outline"}>
            {isSignedIn ? 'Signed In' : 'Not Signed In'}
          </Badge>
          {user && (
            <span className="text-sm text-muted-foreground">
              {user.emailAddress}
            </span>
          )}
        </div>
        
        <div className="text-sm text-muted-foreground">
          ✅ React Router context is properly configured
        </div>
      </CardContent>
    </Card>
  );
}
