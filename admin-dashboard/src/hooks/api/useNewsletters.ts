/**
 * Newsletter API Hooks
 *
 * React hooks for newsletter-related API operations using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  Newsletter,
  NewsletterListParams,
  NewsletterListResponse,
  NewsletterGenerationRequest,
  NewsletterGenerationResponse,
  NewsletterUpdateRequest,
  NewsletterStatsResponse,
  NewsletterStatus
} from '../../../../shared/types/api';
import { apiClient } from '@/services/api/client';
import { queryKeys } from '@/services/query/query-client';

// ============================================================================
// Newsletter List Hook
// ============================================================================

export interface UseNewslettersOptions extends NewsletterListParams {
  enabled?: boolean;
  refetchInterval?: number;
}

export function useNewsletters(options: UseNewslettersOptions = {}) {
  const { enabled = true, refetchInterval, ...params } = options;

  return useQuery({
    queryKey: queryKeys.newsletterList(params),
    queryFn: () => apiClient.getNewsletters(params),
    enabled,
    refetchInterval,
    staleTime: 30000, // 30 seconds
  });
}

// ============================================================================
// Individual Newsletter Hook
// ============================================================================

export function useNewsletter(id: number, options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: queryKeys.newsletter(id),
    queryFn: () => apiClient.getNewsletter(id),
    enabled: enabled && id > 0,
    staleTime: 60000, // 1 minute
  });
}

// ============================================================================
// Newsletter Stats Hook
// ============================================================================

export function useNewsletterStats(options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: queryKeys.newsletterStats(),
    queryFn: () => apiClient.getNewsletterStats(),
    enabled,
    staleTime: 300000, // 5 minutes
  });
}

// ============================================================================
// Newsletter Generation Hook
// ============================================================================

export function useGenerateNewsletter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: NewsletterGenerationRequest) =>
      apiClient.generateNewsletter(request),
    onSuccess: () => {
      // Invalidate newsletter lists and stats
      queryClient.invalidateQueries({ queryKey: ['newsletters'] });
      queryClient.invalidateQueries({ queryKey: ['newsletter-stats'] });
    },
  });
}

// ============================================================================
// Newsletter Status Update Hook
// ============================================================================

export interface UpdateNewsletterStatusParams {
  id: number;
  status: NewsletterStatus;
  title?: string;
  summary?: string;
}

export function useUpdateNewsletterStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...updateData }: UpdateNewsletterStatusParams) =>
      apiClient.updateNewsletterStatus(id, updateData),
    onSuccess: (_, variables) => {
      // Invalidate specific newsletter and lists
      queryClient.invalidateQueries({ queryKey: queryKeys.newsletter(variables.id) });
      queryClient.invalidateQueries({ queryKey: ['newsletters'] });
      queryClient.invalidateQueries({ queryKey: ['newsletter-stats'] });
    },
  });
}

// ============================================================================
// Newsletter Deletion Hook
// ============================================================================

export function useDeleteNewsletter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => apiClient.deleteNewsletter(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache and invalidate lists
      queryClient.removeQueries({ queryKey: queryKeys.newsletter(deletedId) });
      queryClient.invalidateQueries({ queryKey: ['newsletters'] });
      queryClient.invalidateQueries({ queryKey: ['newsletter-stats'] });
    },
  });
}

// ============================================================================
// Newsletter Health Hook
// ============================================================================

export function useNewsletterHealth(options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['newsletter-health'],
    queryFn: () => apiClient.getNewsletterHealth(),
    enabled,
    refetchInterval: 60000, // 1 minute
    staleTime: 30000, // 30 seconds
  });
}

// ============================================================================
// Bulk Newsletter Operations Hook
// ============================================================================

export interface BulkNewsletterOperation {
  newsletter_ids: number[];
  operation: 'delete' | 'archive' | 'publish';
  confirm: boolean;
}

export function useBulkNewsletterOperation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (operation: BulkNewsletterOperation) =>
      apiClient.bulkNewsletterOperation(operation),
    onSuccess: () => {
      // Invalidate all newsletter-related queries
      queryClient.invalidateQueries({ queryKey: ['newsletters'] });
      queryClient.invalidateQueries({ queryKey: ['newsletter-stats'] });
    },
  });
}

// ============================================================================
// Newsletter Search Hook
// ============================================================================

export interface NewsletterSearchParams {
  query?: string;
  status?: NewsletterStatus[];
  newsletter_type?: string[];
  date_from?: string;
  date_to?: string;
  min_quality_score?: number;
  limit?: number;
  offset?: number;
}

export function useNewsletterSearch(params: NewsletterSearchParams, options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['newsletter-search', params],
    queryFn: () => apiClient.searchNewsletters(params),
    enabled: enabled && (params.query || Object.keys(params).length > 0),
    staleTime: 30000, // 30 seconds
  });
}

// ============================================================================
// Newsletter Analytics Hook
// ============================================================================

export function useNewsletterAnalytics(period: string = 'past_30_days', options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['newsletter-analytics', period],
    queryFn: () => apiClient.getNewsletterAnalytics(period),
    enabled,
    staleTime: 300000, // 5 minutes
  });
}

// ============================================================================
// Newsletter Export Hook
// ============================================================================

export function useExportNewsletter() {
  return useMutation({
    mutationFn: ({ id, format }: { id: number; format: 'html' | 'markdown' | 'pdf' }) =>
      apiClient.exportNewsletter(id, format),
  });
}

// ============================================================================
// Newsletter Validation Hook
// ============================================================================

export function useValidateNewsletter() {
  return useMutation({
    mutationFn: (id: number) => apiClient.validateNewsletter(id),
  });
}

// ============================================================================
// Newsletter Preview Hook
// ============================================================================

export function useNewsletterPreview(id: number, options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: ['newsletter-preview', id],
    queryFn: () => apiClient.getNewsletterPreview(id),
    enabled: enabled && id > 0,
    staleTime: 60000, // 1 minute
  });
}
