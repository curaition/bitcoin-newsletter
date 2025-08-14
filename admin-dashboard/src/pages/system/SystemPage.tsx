/**
 * System Page
 *
 * System status, controls, and monitoring. Includes manual ingestion
 * triggers, system health details, and recent activity logs.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Database,
  Play,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Server,
  Zap,
  Settings,
  Loader2
} from 'lucide-react';
import { useSystemStatus } from '@/hooks/api/useSystem';
import { useManualIngest } from '@/hooks/api/useArticles';

export function SystemPage() {
  // Real API data
  const {
    data: systemStatus,
    isLoading: statusLoading,
    error: statusError,
    refetch: refetchStatus
  } = useSystemStatus();

  const manualIngest = useManualIngest();

  const handleManualIngestion = () => {
    manualIngest.mutate({});
  };

  const handleSystemRefresh = () => {
    refetchStatus();
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System</h1>
          <p className="text-muted-foreground">
            System status, controls, and monitoring
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSystemRefresh}
          disabled={statusLoading}
        >
          {statusLoading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh Status
        </Button>
      </div>

      {/* Error Alert */}
      {statusError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load system status. Please check your connection and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Manual Ingestion Status */}
      {manualIngest.isSuccess && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Manual ingestion completed successfully! Check the articles page for new content.
          </AlertDescription>
        </Alert>
      )}

      {manualIngest.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to trigger manual ingestion. Please try again or check system logs.
          </AlertDescription>
        </Alert>
      )}

      {/* System health overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* API Service */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Service</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-6 w-16 bg-muted animate-pulse rounded" />
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="flex items-center space-x-2">
                  {systemStatus?.api?.status === 'healthy' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm font-medium">
                    {systemStatus?.api?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStatus?.api?.version ? `v${systemStatus.api.version}` : 'Version unknown'}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Database */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-6 w-20 bg-muted animate-pulse rounded" />
                <div className="h-4 w-16 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="flex items-center space-x-2">
                  {systemStatus?.database?.status === 'healthy' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm font-medium">
                    {systemStatus?.database?.status === 'healthy' ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStatus?.database?.total_articles || 0} articles
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Task Queue */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Task Queue</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-6 w-16 bg-muted animate-pulse rounded" />
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="flex items-center space-x-2">
                  {systemStatus?.celery?.status === 'healthy' ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm font-medium">
                    {systemStatus?.celery?.status === 'healthy' ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStatus?.celery?.active_tasks?.active || 0} active tasks
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Environment Info */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Environment</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-6 w-20 bg-muted animate-pulse rounded" />
                <div className="h-4 w-16 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="text-sm font-medium">
                  {systemStatus?.environment || 'Unknown'}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {systemStatus?.service || 'crypto-newsletter'}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Manual Ingestion Status Alerts */}
      {manualIngest.isSuccess && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Manual ingestion completed successfully! New articles should appear in the articles page.
          </AlertDescription>
        </Alert>
      )}

      {manualIngest.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to trigger manual ingestion. Please check system status and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* System controls and recent activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* System controls */}
        <Card>
          <CardHeader>
            <CardTitle>System Controls</CardTitle>
            <CardDescription>
              Manual system operations and maintenance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Manual operations should be used carefully. Automated processes are preferred.
              </AlertDescription>
            </Alert>

            <div className="space-y-3">
              <Button
                onClick={handleManualIngestion}
                className="w-full justify-start"
                disabled={manualIngest.isPending}
              >
                {manualIngest.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {manualIngest.isPending ? 'Triggering Ingestion...' : 'Trigger Manual Ingestion'}
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleSystemRefresh}
                disabled={statusLoading}
              >
                {statusLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Refresh System Status
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start"
                disabled
              >
                <Settings className="h-4 w-4 mr-2" />
                View System Configuration
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* System activity log */}
        <Card>
          <CardHeader>
            <CardTitle>Recent System Activity</CardTitle>
            <CardDescription>
              Latest system events and operations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="h-2 w-2 rounded-full bg-green-500 mt-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">Scheduled ingestion completed</p>
                  <p className="text-xs text-muted-foreground">
                    3 articles processed successfully
                  </p>
                  <p className="text-xs text-muted-foreground">2 hours ago</p>
                </div>
                <Badge variant="secondary">Success</Badge>
              </div>

              <Separator />

              <div className="flex items-start space-x-3">
                <div className="h-2 w-2 rounded-full bg-blue-500 mt-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">System health check passed</p>
                  <p className="text-xs text-muted-foreground">
                    All services operational
                  </p>
                  <p className="text-xs text-muted-foreground">4 hours ago</p>
                </div>
                <Badge variant="outline">Info</Badge>
              </div>

              <Separator />

              <div className="flex items-start space-x-3">
                <div className="h-2 w-2 rounded-full bg-yellow-500 mt-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">Database maintenance completed</p>
                  <p className="text-xs text-muted-foreground">
                    Routine optimization performed
                  </p>
                  <p className="text-xs text-muted-foreground">6 hours ago</p>
                </div>
                <Badge variant="outline">Maintenance</Badge>
              </div>

              <Separator />

              <div className="flex items-start space-x-3">
                <div className="h-2 w-2 rounded-full bg-green-500 mt-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium">API service restarted</p>
                  <p className="text-xs text-muted-foreground">
                    Deployment completed successfully
                  </p>
                  <p className="text-xs text-muted-foreground">8 hours ago</p>
                </div>
                <Badge variant="secondary">Deployment</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed system information */}
      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
          <CardDescription>
            Detailed system metrics and configuration
          </CardDescription>
        </CardHeader>
        <CardContent>
          {statusLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="h-4 w-20 bg-muted animate-pulse rounded" />
                  <div className="space-y-1">
                    <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-32 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-28 bg-muted animate-pulse rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Application</h4>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Service: {systemStatus?.service || 'crypto-newsletter'}</p>
                  <p>Environment: {systemStatus?.environment || 'Unknown'}</p>
                  <p>Status: {systemStatus?.overallHealth || 'Unknown'}</p>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Database</h4>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Type: PostgreSQL (Neon)</p>
                  <p>Articles: {systemStatus?.database?.total_articles || 0}</p>
                  <p>Status: {systemStatus?.database?.status || 'Unknown'}</p>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium">Task Processing</h4>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Queue: Celery + Redis</p>
                  <p>Active Tasks: {systemStatus?.celery?.active_tasks?.active || 0}</p>
                  <p>Workers: {systemStatus?.celery?.workers?.workers || 0} online</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
