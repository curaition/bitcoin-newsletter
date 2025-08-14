/**
 * Article Detail Page
 *
 * Displays full article content with metadata and processing information.
 * Includes navigation between articles and external link handling.
 */

import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Calendar,
  User,
  Tag,
  Clock,
  Database,
  AlertCircle
} from 'lucide-react';
import { useArticle, useArticleNavigation } from '@/hooks/api/useArticles';
import { usePublisherLookup } from '@/hooks/api/usePublishers';
import { formatDistanceToNow } from 'date-fns';
import type { Article } from '../../../../shared/types/api';

export function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>();

  // Fetch real article data
  const { data: article, isLoading, error } = useArticle(
    id ? parseInt(id, 10) : 0,
    { enabled: !!id }
  );

  // Publisher lookup for name resolution
  const { getPublisherName } = usePublisherLookup();

  // Article navigation
  const articleId = id ? parseInt(id, 10) : 0;
  const {
    previousArticle,
    nextArticle,
    hasPrevious,
    hasNext,
    currentIndex,
    totalArticles
  } = useArticleNavigation(articleId);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatRelativeDate = (dateString: string) => {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  };

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return <Badge variant="secondary">Active</Badge>;
      case 'PROCESSED':
        return <Badge variant="secondary">Processed</Badge>;
      case 'PENDING':
        return <Badge variant="outline">Pending</Badge>;
      case 'ERROR':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">{status || 'Unknown'}</Badge>;
    }
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return <Badge className="bg-green-100 text-green-800">Positive</Badge>;
      case 'negative':
        return <Badge className="bg-red-100 text-red-800">Negative</Badge>;
      case 'neutral':
        return <Badge variant="outline">Neutral</Badge>;
      default:
        return <Badge variant="outline">{sentiment || 'Unknown'}</Badge>;
    }
  };



  const calculateWordCount = (text: string) => {
    return text ? text.split(/\s+/).filter(word => word.length > 0).length : 0;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 space-y-6">
        <div className="flex items-center space-x-4">
          <div className="h-10 w-32 bg-muted animate-pulse rounded" />
          <div className="h-6 w-24 bg-muted animate-pulse rounded" />
        </div>
        <div className="h-8 w-3/4 bg-muted animate-pulse rounded" />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="h-64 w-full bg-muted animate-pulse rounded" />
          </div>
          <div className="space-y-4">
            <div className="h-32 w-full bg-muted animate-pulse rounded" />
            <div className="h-24 w-full bg-muted animate-pulse rounded" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Error Loading Article</h2>
          <p className="text-muted-foreground mb-4">
            {error instanceof Error ? error.message : 'Failed to load article'}
          </p>
          <Button asChild>
            <Link to="/articles">Back to Articles</Link>
          </Button>
        </div>
      </div>
    );
  }

  // Article not found
  if (!article) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold mb-2">Article not found</h2>
          <p className="text-muted-foreground mb-4">
            The article you're looking for doesn't exist or has been removed.
          </p>
          <Button asChild>
            <Link to="/articles">Back to Articles</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="/articles">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Articles
            </Link>
          </Button>
          <div className="text-sm text-muted-foreground">
            Article #{article.id} ({currentIndex + 1} of {totalArticles})
          </div>
        </div>

        {/* Previous/Next Navigation */}
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!hasPrevious}
            asChild={hasPrevious}
          >
            {hasPrevious ? (
              <Link to={`/articles/${previousArticle!.id}`}>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Link>
            ) : (
              <>
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </>
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            disabled={!hasNext}
            asChild={hasNext}
          >
            {hasNext ? (
              <Link to={`/articles/${nextArticle!.id}`}>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            ) : (
              <>
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Article header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-2xl">{article.title}</CardTitle>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <User className="h-4 w-4" />
                  <span>{getPublisherName(article.publisher_id)}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(article.published_on)}</span>
                </div>
                {article.authors && (
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>by {article.authors}</span>
                  </div>
                )}
              </div>
            </div>
            <Button variant="outline" size="sm" asChild>
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                View Original
              </a>
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Article metadata and content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main content */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Article Content</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <div className="text-base leading-relaxed whitespace-pre-wrap">
                  {article.body || 'No content available'}
                </div>
                {article.subtitle && (
                  <div className="mt-4 p-4 bg-muted rounded-lg">
                    <h3 className="font-medium mb-2">Subtitle</h3>
                    <p className="text-sm text-muted-foreground">{article.subtitle}</p>
                  </div>
                )}
                {article.keywords && (
                  <div className="mt-4">
                    <h3 className="font-medium mb-2">Keywords</h3>
                    <div className="flex flex-wrap gap-1">
                      {article.keywords.split('|').map((keyword, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {keyword.trim()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Metadata sidebar */}
        <div className="space-y-6">
          {/* Processing info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Processing Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Status</span>
                {getStatusBadge(article.status)}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Language</span>
                <Badge variant="outline">
                  <Tag className="h-3 w-3 mr-1" />
                  {article.language || 'Unknown'}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">External ID</span>
                <span className="text-sm font-mono">{article.external_id}</span>
              </div>

              <Separator />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Word Count</span>
                  <span className="text-sm font-medium">{calculateWordCount(article.body || '')}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Created</span>
                  <span className="text-sm font-medium">
                    {formatRelativeDate(article.created_at)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Updated</span>
                  <span className="text-sm font-medium">
                    {formatRelativeDate(article.updated_at)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Database className="h-4 w-4 mr-2" />
                Reprocess Article
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Clock className="h-4 w-4 mr-2" />
                View Processing Log
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
