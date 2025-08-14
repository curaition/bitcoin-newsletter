/**
 * Articles Page
 *
 * Browse and search articles with pagination and filtering.
 * Displays articles in a responsive table format.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Search,
  ExternalLink,
  Calendar,
  User,
  Loader2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { useArticles } from '@/hooks/api/useArticles';
import { usePublisherLookup } from '@/hooks/api/usePublishers';
import { formatDistanceToNow } from 'date-fns';
import type { ArticleListParams } from '../../../../shared/types/api';

export function ArticlesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<ArticleListParams>({
    limit: 20,
    page: 1,
    orderBy: 'published_on',
    order: 'desc'
  });

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1); // Reset to first page on search
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Update filters when search or page changes
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      search: debouncedSearch || undefined,
      page: currentPage
    }));
  }, [debouncedSearch, currentPage]);

  // Real API data
  const {
    data: articlesResponse,
    isLoading,
    error,
    refetch
  } = useArticles(filters);

  // Publisher lookup for name resolution
  const { getPublisherName } = usePublisherLookup();

  const formatDate = (dateString: string) => {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'ACTIVE':
        return <Badge variant="secondary">Active</Badge>;
      case 'INACTIVE':
        return <Badge variant="outline">Inactive</Badge>;
      case 'DELETED':
        return <Badge variant="destructive">Deleted</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleSearch = () => {
    setDebouncedSearch(searchQuery);
    setCurrentPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Articles</h1>
          <p className="text-muted-foreground">
            Browse and manage ingested articles
          </p>
        </div>
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
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load articles. Please check your connection and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search Articles</CardTitle>
          <CardDescription>
            Find articles by title, publisher, or content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search articles..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10"
                />
              </div>
            </div>
            <Button onClick={handleSearch} disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Search className="h-4 w-4 mr-2" />
              )}
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Articles table */}
      <Card>
        <CardHeader>
          <CardTitle>Articles</CardTitle>
          <CardDescription>
            {isLoading ? (
              'Loading articles...'
            ) : articlesResponse?.pagination ? (
              `${articlesResponse.pagination.total} articles found`
            ) : (
              'No articles found'
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="h-4 w-4 bg-muted animate-pulse rounded" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-1/2 bg-muted animate-pulse rounded" />
                  </div>
                  <div className="h-6 w-16 bg-muted animate-pulse rounded" />
                </div>
              ))}
            </div>
          ) : articlesResponse?.articles?.length ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Publisher</TableHead>
                  <TableHead>Published</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {articlesResponse.articles.map((article) => (
                  <TableRow key={article.id}>
                    <TableCell>
                      <div className="space-y-1 max-w-md">
                        <Link
                          to={`/articles/${article.id}`}
                          className="font-medium hover:underline line-clamp-2"
                        >
                          {article.title}
                        </Link>
                        {article.summary && (
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {article.summary}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">
                          {getPublisherName(article.publisher_id)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{formatDate(article.published_on)}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(article.status)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/articles/${article.id}`}>
                            <ExternalLink className="h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                {debouncedSearch ? 'No articles found matching your search.' : 'No articles available.'}
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-4"
                onClick={() => refetch()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {articlesResponse?.pagination && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {articlesResponse.pagination.offset + 1} to{' '}
            {Math.min(
              articlesResponse.pagination.offset + articlesResponse.pagination.limit,
              articlesResponse.pagination.total
            )}{' '}
            of {articlesResponse.pagination.total} articles
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={!articlesResponse.pagination.hasPrevious || isLoading}
            >
              Previous
            </Button>
            <span className="flex items-center px-3 text-sm text-muted-foreground">
              Page {currentPage}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!articlesResponse.pagination.hasNext || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
