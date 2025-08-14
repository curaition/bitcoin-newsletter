/**
 * Dashboard Page
 *
 * Main dashboard overview with system health, recent activity,
 * and quick actions. Auto-refreshes every 30 seconds.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity,
  Database,
  FileText,
  TrendingUp,
  RefreshCw,
  Play,
  AlertCircle,
  CheckCircle,
  Loader2,
  Zap
} from 'lucide-react';
import { useSystemStatus } from '@/hooks/api/useSystem';
import { useArticles } from '@/hooks/api/useArticles';
import { useManualIngest } from '@/hooks/api/useArticles';
import { formatDistanceToNow } from 'date-fns';

export function DashboardPage() {
  // Real API data instead of mock data
  const {
    data: systemStatus,
    isLoading: statusLoading,
    error: statusError,
    refetch: refetchStatus
  } = useSystemStatus();

  const {
    data: recentArticles,
    isLoading: articlesLoading
  } = useArticles({
    limit: 5,
    orderBy: 'created_at',
    order: 'desc'
  });

  const manualIngest = useManualIngest();

  const handleRefresh = () => {
    refetchStatus();
  };

  const handleManualIngestion = () => {
    manualIngest.mutate({});
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            System overview and quick actions
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={statusLoading}
        >
          {statusLoading ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4 mr-2" />
          )}
          Refresh
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

      {/* System health cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* API Service Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Service</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-8 w-20 bg-muted animate-pulse rounded" />
                <div className="h-4 w-16 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {systemStatus?.api?.status === 'healthy' ? 'Online' : 'Offline'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  <Badge
                    variant={systemStatus?.api?.status === 'healthy' ? 'secondary' : 'destructive'}
                    className="text-xs"
                  >
                    {systemStatus?.api?.status || 'Unknown'}
                  </Badge>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Database Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Database</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-8 w-24 bg-muted animate-pulse rounded" />
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {systemStatus?.database?.status === 'healthy' ? 'Connected' : 'Disconnected'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  <Badge variant="secondary" className="text-xs">
                    {systemStatus?.database?.total_articles || 0} articles
                  </Badge>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Task Queue Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Task Queue</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-8 w-16 bg-muted animate-pulse rounded" />
                <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {systemStatus?.celery?.status === 'healthy' ? 'Active' : 'Inactive'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  <Badge variant="outline" className="text-xs">
                    {systemStatus?.celery?.active_tasks?.active || 0} active
                  </Badge>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Total Articles */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {statusLoading ? (
              <div className="space-y-2">
                <div className="h-8 w-12 bg-muted animate-pulse rounded" />
                <div className="h-4 w-16 bg-muted animate-pulse rounded" />
              </div>
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {systemStatus?.database?.total_articles || 0}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  <TrendingUp className="h-3 w-3 inline mr-1" />
                  {recentArticles?.articles?.length || 0} recent
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick actions and recent activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quick actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common administrative tasks
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              className="w-full justify-start"
              onClick={handleManualIngestion}
              disabled={manualIngest.isPending}
            >
              {manualIngest.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {manualIngest.isPending ? 'Triggering...' : 'Trigger Manual Ingestion'}
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => window.location.href = '/articles'}
            >
              <FileText className="h-4 w-4 mr-2" />
              View Latest Articles
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => window.location.href = '/system'}
            >
              <Activity className="h-4 w-4 mr-2" />
              System Status Details
            </Button>
          </CardContent>
        </Card>

        {/* Recent activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Articles</CardTitle>
            <CardDescription>
              Latest ingested articles
            </CardDescription>
          </CardHeader>
          <CardContent>
            {articlesLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center space-x-3">
                    <div className="h-2 w-2 rounded-full bg-muted animate-pulse" />
                    <div className="flex-1 space-y-1">
                      <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                      <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recentArticles?.articles?.length ? (
              <div className="space-y-4">
                {recentArticles.articles.slice(0, 3).map((article) => (
                  <div key={article.id} className="flex items-center space-x-3">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <div className="flex-1">
                      <p className="text-sm font-medium line-clamp-1">{article.title}</p>
                      <p className="text-xs text-muted-foreground">
                        Publisher ID: {article.publisher_id || 'Unknown'} • {' '}
                        {formatDistanceToNow(new Date(article.published_on), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                ))}
                {recentArticles.articles.length > 3 && (
                  <div className="pt-2 border-t">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full"
                      onClick={() => window.location.href = '/articles'}
                    >
                      View all {recentArticles.pagination?.total || recentArticles.articles.length} articles
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground">No articles found</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={handleManualIngestion}
                  disabled={manualIngest.isPending}
                >
                  {manualIngest.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Trigger Ingestion
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Manual Ingestion Status */}
      {manualIngest.isSuccess && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Manual ingestion completed successfully! New articles should appear shortly.
          </AlertDescription>
        </Alert>
      )}

      {manualIngest.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to trigger manual ingestion. Please try again or check system status.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
