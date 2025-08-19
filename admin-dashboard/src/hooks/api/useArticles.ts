/**
 * Article API Hooks
 *
 * React hooks for article-related API operations using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  Article,
  ArticleListParams,
  ManualIngestRequest,
  IngestionResult
} from '../../../../shared/types/api';
import { apiClient } from '@/services/api/client';
import { queryKeys, queryInvalidation } from '@/services/query/query-client';
// import { createCacheKey } from '../../../../shared/utils/api-helpers';

// ============================================================================
// Article List Hook
// ============================================================================

export interface UseArticlesOptions extends ArticleListParams {
  enabled?: boolean;
  refetchInterval?: number;
}

export function useArticles(options: UseArticlesOptions = {}) {
  const { enabled = true, refetchInterval, ...params } = options;

  return useQuery({
    queryKey: queryKeys.articleList(params),
    queryFn: () => apiClient.getArticles(params),
    enabled,
    refetchInterval,
    select: (data: Article[]) => {
      // Transform simple array to expected structure
      const limit = params.limit || 20;
      const page = params.page || 1;
      const offset = params.offset || ((page - 1) * limit);

      return {
        articles: data,
        pagination: {
          total: data.length, // Note: This is not accurate for real pagination
          page,
          limit,
          offset,
          hasNext: data.length === limit, // Rough estimate
          hasPrevious: page > 1,
        }
      };
    },
  });
}

// ============================================================================
// Single Article Hook
// ============================================================================

export function useArticle(id: number, options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;

  return useQuery({
    queryKey: queryKeys.article(id),
    queryFn: () => apiClient.getArticle(id),
    enabled: enabled && !!id,
  });
}

// ============================================================================
// Analysis-Ready Articles Hook
// ============================================================================

export function useAnalysisReadyArticles(options: UseArticlesOptions = {}) {
  const { enabled = true, refetchInterval, ...params } = options;

  return useQuery({
    queryKey: [...queryKeys.articles, 'analysis-ready', params],
    queryFn: () => apiClient.getAnalysisReadyArticles(params),
    enabled,
    refetchInterval,
    select: (data: Article[]) => {
      // Transform simple array to expected structure
      const limit = params.limit || 20;
      const page = params.page || 1;
      const offset = params.offset || ((page - 1) * limit);

      return {
        articles: data,
        pagination: {
          total: data.length,
          page,
          limit,
          offset,
          hasNext: data.length === limit,
          hasPrevious: page > 1,
        }
      };
    },
  });
}

// ============================================================================
// Article Search Hook
// ============================================================================

export function useArticleSearch(searchQuery: string, options: Omit<ArticleListParams, 'search'> = {}) {
  const params = { ...options, search: searchQuery };

  return useQuery({
    queryKey: queryKeys.articleList(params),
    queryFn: () => apiClient.getArticles(params),
    enabled: searchQuery.length >= 2, // Only search with 2+ characters
    select: (data: Article[]) => ({
      articles: data,
      pagination: {
        total: data.length,
        page: 1,
        limit: data.length,
        offset: 0,
        hasNext: false,
        hasPrevious: false,
      },
    }),
  });
}

// ============================================================================
// Infinite Articles Hook (for pagination)
// ============================================================================

import { useInfiniteQuery } from '@tanstack/react-query';

export function useInfiniteArticles(params: Omit<ArticleListParams, 'page' | 'offset'> = {}) {
  return useInfiniteQuery({
    queryKey: [...queryKeys.articles, 'infinite', params],
    queryFn: ({ pageParam = 1 }) =>
      apiClient.getArticles({ ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage: Article[], allPages) => {
      // Since we get a simple array, estimate if there are more pages
      const limit = params.limit || 20;
      return lastPage.length === limit ? allPages.length + 1 : undefined;
    },
    select: (data) => ({
      pages: data.pages,
      articles: data.pages.flatMap(page => page),
      totalCount: data.pages.reduce((total, page) => total + page.length, 0),
    }),
  });
}

// ============================================================================
// Manual Ingestion Hook
// ============================================================================

export function useManualIngest() {
  // const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: ManualIngestRequest) =>
      apiClient.triggerManualIngest(params),
    onSuccess: (result: IngestionResult) => {
      // Invalidate article lists to show new articles
      queryInvalidation.articleList();

      // Invalidate system status to show updated stats
      queryInvalidation.system();

      console.log('Manual ingestion completed:', result);
    },
    onError: (error) => {
      console.error('Manual ingestion failed:', error);
    },
  });
}

// ============================================================================
// Prefetch Helpers
// ============================================================================

export function usePrefetchArticle() {
  const queryClient = useQueryClient();

  return (id: number) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.article(id),
      queryFn: () => apiClient.getArticle(id),
      staleTime: 5 * 60 * 1000, // 5 minutes
    });
  };
}

export function usePrefetchArticles() {
  const queryClient = useQueryClient();

  return (params: ArticleListParams = {}) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.articleList(params),
      queryFn: () => apiClient.getArticles(params),
      staleTime: 2 * 60 * 1000, // 2 minutes
    });
  };
}

// ============================================================================
// Article Navigation Hook
// ============================================================================

export function useArticleNavigation(currentArticleId: number) {
  const { data: articlesResponse } = useArticles({
    limit: 100, // Get more articles for navigation
    orderBy: 'published_on',
    order: 'desc'
  });

  // Extract articles array from response
  const articles = articlesResponse?.articles || [];

  // Find current article index
  const currentIndex = articles.findIndex(article => article.id === currentArticleId);

  // Get previous and next articles
  const previousArticle = currentIndex > 0 ? articles[currentIndex - 1] : null;
  const nextArticle = currentIndex < articles.length - 1 ? articles[currentIndex + 1] : null;

  return {
    previousArticle,
    nextArticle,
    hasPrevious: !!previousArticle,
    hasNext: !!nextArticle,
    currentIndex,
    totalArticles: articles.length,
  };
}

// ============================================================================
// Cache Utilities
// ============================================================================

export function useArticleCache() {
  const queryClient = useQueryClient();

  return {
    // Get cached article
    getCachedArticle: (id: number): Article | undefined => {
      return queryClient.getQueryData(queryKeys.article(id));
    },

    // Set article in cache
    setCachedArticle: (id: number, article: Article) => {
      queryClient.setQueryData(queryKeys.article(id), article);
    },

    // Remove article from cache
    removeCachedArticle: (id: number) => {
      queryClient.removeQueries({ queryKey: queryKeys.article(id) });
    },

    // Get cached article list
    getCachedArticleList: (params: ArticleListParams = {}): any => {
      return queryClient.getQueryData(queryKeys.articleList(params));
    },

    // Update article in all relevant caches
    updateArticleInCache: (id: number, updater: (article: Article) => Article) => {
      // Update single article cache
      queryClient.setQueryData(queryKeys.article(id), (old: Article | undefined) =>
        old ? updater(old) : undefined
      );

      // Update article in list caches
      queryClient.setQueriesData(
        { queryKey: queryKeys.articles, predicate: (query) => query.queryKey[1] === 'list' },
        (old: any) => {
          if (!old) return old;

          return {
            ...old,
            articles: old.articles?.map((article: Article) =>
              article.id === id ? updater(article) : article
            ) || [],
          };
        }
      );
    },
  };
}
