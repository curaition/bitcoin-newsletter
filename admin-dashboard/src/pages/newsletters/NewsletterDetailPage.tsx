/**
 * Newsletter Detail Page
 *
 * View and manage individual newsletter details with content preview,
 * status management, and generation metadata.
 */

import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
// Select component temporarily removed - using basic HTML select
import {
  ArrowLeft,
  Calendar,
  FileText,
  Star,
  Clock,
  DollarSign,
  Loader2,
  AlertCircle,
  RefreshCw,
  Eye,
  Code,
  Edit,
  Trash2,

} from 'lucide-react';
import { useNewsletter, useUpdateNewsletterStatus, useDeleteNewsletter } from '@/hooks/api/useNewsletters';
import { formatDistanceToNow } from 'date-fns';
import type { NewsletterStatus } from '../../../../shared/types/api';
import { NEWSLETTER_STATUS_OPTIONS } from '../../../../shared/types/api';

export function NewsletterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedStatus, setSelectedStatus] = useState<NewsletterStatus | ''>('');

  const newsletterId = parseInt(id || '0', 10);

  // Newsletter data
  const {
    data: newsletter,
    isLoading,
    error,
    refetch
  } = useNewsletter(newsletterId);

  // Status update mutation
  const updateStatusMutation = useUpdateNewsletterStatus();

  // Delete mutation
  const deleteMutation = useDeleteNewsletter();

  const handleStatusUpdate = async () => {
    if (!selectedStatus || !newsletter) return;

    try {
      await updateStatusMutation.mutateAsync({
        id: newsletter.id,
        status: selectedStatus
      });
      setSelectedStatus('');
      refetch();
    } catch (error) {
      console.error('Failed to update newsletter status:', error);
    }
  };

  const handleDelete = async () => {
    if (!newsletter) return;

    if (window.confirm(`Are you sure you want to delete "${newsletter.title}"? This action cannot be undone.`)) {
      try {
        await deleteMutation.mutateAsync(newsletter.id);
        navigate('/newsletters');
      } catch (error) {
        console.error('Failed to delete newsletter:', error);
      }
    }
  };

  const getStatusBadge = (status: NewsletterStatus) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'REVIEW':
        return <Badge variant="secondary">Review</Badge>;
      case 'PUBLISHED':
        return <Badge variant="default">Published</Badge>;
      case 'ARCHIVED':
        return <Badge variant="destructive">Archived</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type.toUpperCase()) {
      case 'DAILY':
        return <Badge variant="outline">Daily</Badge>;
      case 'WEEKLY':
        return <Badge variant="secondary">Weekly</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  const getQualityBadge = (score: number | null) => {
    if (!score) return <Badge variant="outline">No Score</Badge>;

    if (score >= 0.8) {
      return <Badge variant="default"><Star className="h-3 w-3 mr-1" />High ({score.toFixed(2)})</Badge>;
    } else if (score >= 0.6) {
      return <Badge variant="secondary">Good ({score.toFixed(2)})</Badge>;
    } else {
      return <Badge variant="outline">Fair ({score.toFixed(2)})</Badge>;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const getNewsletterType = (): string => {
    return newsletter?.generation_metadata?.newsletter_type || 'UNKNOWN';
  };

  const getGenerationCost = (): number | null => {
    return newsletter?.generation_metadata?.generation_cost || null;
  };

  const getProcessingTime = (): number | null => {
    return newsletter?.generation_metadata?.processing_time_seconds || null;
  };

  const getArticlesProcessed = (): number | null => {
    return newsletter?.generation_metadata?.articles_processed || null;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <div className="h-8 w-8 bg-muted animate-pulse rounded" />
          <div className="flex-1 space-y-2">
            <div className="h-6 w-1/3 bg-muted animate-pulse rounded" />
            <div className="h-4 w-1/4 bg-muted animate-pulse rounded" />
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <div className="h-64 bg-muted animate-pulse rounded" />
          <div className="h-64 bg-muted animate-pulse rounded" />
        </div>
      </div>
    );
  }

  if (error || !newsletter) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/newsletters">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Newsletters
            </Link>
          </Button>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error ? 'Failed to load newsletter details.' : 'Newsletter not found.'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/newsletters">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Newsletters
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{newsletter.title}</h1>
            <div className="flex items-center space-x-2 mt-1">
              {getTypeBadge(getNewsletterType())}
              {getStatusBadge(newsletter.status)}
              {getQualityBadge(newsletter.quality_score)}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4 mr-2" />
            )}
            Delete
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Newsletter Info */}
        <div className="md:col-span-2 space-y-6">
          {/* Content Preview */}
          <Card>
            <CardHeader>
              <CardTitle>Content Preview</CardTitle>
              <CardDescription>
                Newsletter content and summary
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {newsletter.summary && (
                <div>
                  <h4 className="font-medium mb-2">Summary</h4>
                  <p className="text-sm text-muted-foreground">{newsletter.summary}</p>
                </div>
              )}
              <Separator />
              <div>
                <h4 className="font-medium mb-2">Content</h4>
                <Tabs defaultValue="markdown" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="markdown" className="flex items-center gap-2">
                      <Code className="h-4 w-4" />
                      Markdown
                    </TabsTrigger>
                    <TabsTrigger value="preview" className="flex items-center gap-2">
                      <Eye className="h-4 w-4" />
                      Preview
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="markdown" className="mt-4">
                    <div className="prose prose-sm max-w-none">
                      <div className="text-sm whitespace-pre-wrap bg-muted/50 p-4 rounded-md max-h-[600px] overflow-y-auto font-mono">
                        {newsletter.content}
                      </div>
                    </div>
                  </TabsContent>
                  <TabsContent value="preview" className="mt-4">
                    <div className="prose prose-sm max-w-none">
                      <div
                        className="bg-white p-6 rounded-md border max-h-[600px] overflow-y-auto"
                        dangerouslySetInnerHTML={{
                          __html: newsletter.content
                            .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-orange-500 border-b-2 border-orange-500 pb-2 mb-4">$1</h1>')
                            .replace(/^## (.+)$/gm, '<h2 class="text-xl font-semibold text-gray-800 mt-6 mb-3">$1</h2>')
                            .replace(/^### (.+)$/gm, '<h3 class="text-lg font-medium text-gray-700 mt-4 mb-2">$1</h3>')
                            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*(.+?)\*/g, '<em>$1</em>')
                            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-orange-500 hover:underline" target="_blank" rel="noopener noreferrer">$1</a>')
                            .replace(/\n\n/g, '</p><p class="mb-4">')
                            .replace(/^(.+)$/gm, '<p class="mb-4">$1</p>')
                            .replace(/<p class="mb-4"><h/g, '<h')
                            .replace(/<\/h([1-6])><\/p>/g, '</h$1>')
                        }}
                      />
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status Management */}
          <Card>
            <CardHeader>
              <CardTitle>Status Management</CardTitle>
              <CardDescription>
                Update newsletter status
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Current Status</label>
                <div>{getStatusBadge(newsletter.status)}</div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Update Status</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value as NewsletterStatus)}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="">Select new status</option>
                  {NEWSLETTER_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                onClick={handleStatusUpdate}
                disabled={!selectedStatus || selectedStatus === newsletter.status || updateStatusMutation.isPending}
                className="w-full"
              >
                {updateStatusMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Edit className="h-4 w-4 mr-2" />
                )}
                Update Status
              </Button>
            </CardContent>
          </Card>

          {/* Newsletter Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
              <CardDescription>
                Newsletter metadata and generation info
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Generated</span>
                  <div className="flex items-center space-x-1">
                    <Calendar className="h-3 w-3" />
                    <span className="text-sm">{formatDistanceToNow(new Date(newsletter.generation_date), { addSuffix: true })}</span>
                  </div>
                </div>

                {newsletter.published_at && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Published</span>
                    <div className="flex items-center space-x-1">
                      <Calendar className="h-3 w-3" />
                      <span className="text-sm">{formatDistanceToNow(new Date(newsletter.published_at), { addSuffix: true })}</span>
                    </div>
                  </div>
                )}

                {getGenerationCost() && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Generation Cost</span>
                    <div className="flex items-center space-x-1">
                      <DollarSign className="h-3 w-3" />
                      <span className="text-sm">{formatCurrency(getGenerationCost()!)}</span>
                    </div>
                  </div>
                )}

                {getProcessingTime() && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Processing Time</span>
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span className="text-sm">{formatDuration(getProcessingTime()!)}</span>
                    </div>
                  </div>
                )}

                {getArticlesProcessed() && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Articles Processed</span>
                    <div className="flex items-center space-x-1">
                      <FileText className="h-3 w-3" />
                      <span className="text-sm">{getArticlesProcessed()}</span>
                    </div>
                  </div>
                )}

                {newsletter.agent_version && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Agent Version</span>
                    <span className="text-sm font-mono">{newsletter.agent_version}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
