/**
 * Newsletters Page
 *
 * Browse and manage newsletters with pagination and filtering.
 * Displays newsletters in a responsive table format.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
// Select component temporarily removed - using basic HTML select
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
  FileText,
  Loader2,
  AlertCircle,
  RefreshCw,
  Plus,
  Star,

} from 'lucide-react';
import { useNewsletters } from '@/hooks/api/useNewsletters';
import { formatDistanceToNow } from 'date-fns';
import type { NewsletterListParams, NewsletterStatus, NewsletterType } from '../../../../shared/types/api';
import { NEWSLETTER_STATUS_OPTIONS, NEWSLETTER_TYPE_OPTIONS } from '../../../../shared/types/api';

export function NewslettersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<NewsletterStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<NewsletterType | 'all'>('all');
  const [filters, setFilters] = useState<NewsletterListParams>({
    limit: 20,
    page: 1,
    orderBy: 'generation_date',
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

  // Update filters when search, page, or filters change
  useEffect(() => {
    setFilters(prev => ({
      ...prev,
      page: currentPage,
      status: statusFilter === 'all' ? undefined : statusFilter,
      newsletter_type: typeFilter === 'all' ? undefined : typeFilter,
    }));
  }, [currentPage, statusFilter, typeFilter]);

  // Newsletter data
  const {
    data: newslettersResponse,
    isLoading,
    error,
    refetch
  } = useNewsletters(filters);

  const formatDate = (dateString: string) => {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
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
        return <Badge variant="outline" className="text-xs">Daily</Badge>;
      case 'WEEKLY':
        return <Badge variant="secondary" className="text-xs">Weekly</Badge>;
      default:
        return <Badge variant="outline" className="text-xs">{type}</Badge>;
    }
  };

  const getQualityBadge = (score: number | null) => {
    if (!score) return null;

    if (score >= 0.8) {
      return <Badge variant="default" className="text-xs"><Star className="h-3 w-3 mr-1" />High</Badge>;
    } else if (score >= 0.6) {
      return <Badge variant="secondary" className="text-xs">Good</Badge>;
    } else {
      return <Badge variant="outline" className="text-xs">Fair</Badge>;
    }
  };

  const handleSearch = () => {
    setDebouncedSearch(searchQuery);
    setCurrentPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const getNewsletterType = (newsletter: any): string => {
    return newsletter.generation_metadata?.newsletter_type || 'UNKNOWN';
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Newsletters</h1>
          <p className="text-muted-foreground">
            Browse and manage generated newsletters
          </p>
        </div>
        <div className="flex gap-2">
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
          <Button size="sm" asChild>
            <Link to="/newsletters/generate">
              <Plus className="h-4 w-4 mr-2" />
              Generate Newsletter
            </Link>
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load newsletters. Please check your connection and try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Search and filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search & Filter Newsletters</CardTitle>
          <CardDescription>
            Find newsletters by title, status, or type
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search newsletters..."
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

            {/* Filters */}
            <div className="flex gap-4">
              <div className="flex-1">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as NewsletterStatus | 'all')}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="all">All Statuses</option>
                  {NEWSLETTER_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value as NewsletterType | 'all')}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="all">All Types</option>
                  {NEWSLETTER_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Newsletters table */}
      <Card>
        <CardHeader>
          <CardTitle>Newsletters</CardTitle>
          <CardDescription>
            {isLoading ? (
              'Loading newsletters...'
            ) : newslettersResponse ? (
              `${newslettersResponse.total_count} newsletters found`
            ) : (
              'No newsletters found'
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
          ) : newslettersResponse?.newsletters?.length ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Quality</TableHead>
                  <TableHead>Generated</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {newslettersResponse.newsletters.map((newsletter) => (
                  <TableRow key={newsletter.id}>
                    <TableCell>
                      <div className="space-y-1 max-w-md">
                        <Link
                          to={`/newsletters/${newsletter.id}`}
                          className="font-medium hover:underline line-clamp-2"
                        >
                          {newsletter.title}
                        </Link>
                        {newsletter.summary && (
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {newsletter.summary}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {getTypeBadge(getNewsletterType(newsletter))}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(newsletter.status)}
                    </TableCell>
                    <TableCell>
                      {getQualityBadge(newsletter.quality_score)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{formatDate(newsletter.generation_date)}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Button variant="ghost" size="sm" asChild>
                          <Link to={`/newsletters/${newsletter.id}`}>
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
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                {debouncedSearch ? 'No newsletters found matching your search.' : 'No newsletters available.'}
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
      {newslettersResponse && newslettersResponse.total_count > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * filters.limit!) + 1} to{' '}
            {Math.min(currentPage * filters.limit!, newslettersResponse.total_count)}{' '}
            of {newslettersResponse.total_count} newsletters
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1 || isLoading}
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
              disabled={!newslettersResponse.has_more || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
