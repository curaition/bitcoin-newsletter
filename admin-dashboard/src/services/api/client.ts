/**
 * API Client for Bitcoin Newsletter Admin Dashboard
 *
 * Uses shared types for type-safe API communication with the FastAPI backend
 */

import type {
  Article,
  Publisher,
  ArticleListParams,
  SystemStatusResponse,
  LoginRequest,
  LoginResponse,
  ManualIngestRequest,
  IngestionResult,
  TaskStatusResponse,
  Newsletter,
  NewsletterListParams,
  NewsletterListResponse,
  NewsletterGenerationRequest,
  NewsletterGenerationResponse,
  NewsletterUpdateRequest,
  NewsletterStatsResponse,
} from '../../../../shared/types/api';

import {
  buildApiUrl,
  processApiResponse,
  createAuthHeaders,
  withRetry,
  DEFAULT_RETRY_OPTIONS,
  APIError as SharedAPIError,
} from '../../../../shared/utils/api-helpers';

import { config, API_ENDPOINTS } from '@/utils/env';

export class AdminAPIClient {
  private baseUrl: string;
  private getToken: () => string | null;

  constructor(baseUrl: string, getToken: () => string | null) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  // ============================================================================
  // Authentication Methods
  // ============================================================================

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.login);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const result = await processApiResponse<LoginResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async logout(): Promise<void> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.logout);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      const result = await processApiResponse(response);
      throw new SharedAPIError(result.status, result.error?.message || 'Logout failed');
    }
  }

  async refreshToken(): Promise<LoginResponse> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.refresh);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, {
      method: 'POST',
      headers,
    });

    const result = await processApiResponse<LoginResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  // ============================================================================
  // Article Methods
  // ============================================================================

  async getArticles(params: ArticleListParams = {}): Promise<Article[]> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.articles, params);
    const headers = createAuthHeaders(this.getToken());

    const fetchArticles = async () => {
      const response = await fetch(url, { headers });
      const result = await processApiResponse<Article[]>(response);

      if (result.error) {
        throw new SharedAPIError(result.status, result.error.message, result.error.code);
      }

      return result.data!;
    };

    return withRetry(fetchArticles, DEFAULT_RETRY_OPTIONS);
  }

  async getArticle(id: number): Promise<Article> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.article(id));
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<Article>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getAnalysisReadyArticles(params: ArticleListParams = {}): Promise<Article[]> {
    const url = buildApiUrl(this.baseUrl, `${API_ENDPOINTS.articles}/analysis-ready`, params);
    const headers = createAuthHeaders(this.getToken());

    const fetchArticles = async () => {
      const response = await fetch(url, { headers });
      const result = await processApiResponse<Article[]>(response);

      if (result.error) {
        throw new SharedAPIError(result.status, result.error.message, result.error.code);
      }

      return result.data!;
    };

    return withRetry(fetchArticles, DEFAULT_RETRY_OPTIONS);
  }

  // ============================================================================
  // Publisher Methods
  // ============================================================================

  async getPublishers(): Promise<Publisher[]> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.publishers);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<Publisher[]>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  // ============================================================================
  // System Status Methods
  // ============================================================================

  async getSystemStatus(): Promise<SystemStatusResponse> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.adminStatus);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<SystemStatusResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getHealthCheck(): Promise<{ status: string; timestamp: string }> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.health);

    const response = await fetch(url);
    const result = await processApiResponse<{ status: string; timestamp: string }>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  // ============================================================================
  // Admin Operations
  // ============================================================================

  async triggerManualIngest(params: ManualIngestRequest = {}): Promise<IngestionResult> {
    const url = buildApiUrl(this.baseUrl, API_ENDPOINTS.adminIngest);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(params),
    });

    const result = await processApiResponse<IngestionResult>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const url = buildApiUrl(this.baseUrl, `${API_ENDPOINTS.adminTasks}/${taskId}`);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<TaskStatusResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  // ============================================================================
  // Newsletter Methods
  // ============================================================================

  async getNewsletters(params: NewsletterListParams = {}): Promise<NewsletterListResponse> {
    const url = buildApiUrl(this.baseUrl, '/api/newsletters', params);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<NewsletterListResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getNewsletter(id: number): Promise<Newsletter> {
    const url = buildApiUrl(this.baseUrl, `/api/newsletters/${id}`);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<Newsletter>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async generateNewsletter(request: NewsletterGenerationRequest): Promise<NewsletterGenerationResponse> {
    const url = buildApiUrl(this.baseUrl, '/admin/newsletters/generate');
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    const result = await processApiResponse<NewsletterGenerationResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async updateNewsletterStatus(id: number, updateData: NewsletterUpdateRequest): Promise<any> {
    // Admin endpoint expects query parameters, not JSON body
    const params: Record<string, any> = {};
    if (updateData.status) params.status = updateData.status;
    if (updateData.title) params.title = updateData.title;
    if (updateData.summary) params.summary = updateData.summary;

    const url = buildApiUrl(this.baseUrl, `/admin/newsletters/${id}/status`, params);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, {
      method: 'PUT',
      headers,
    });

    const result = await processApiResponse(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async deleteNewsletter(id: number): Promise<any> {
    const url = buildApiUrl(this.baseUrl, `/admin/newsletters/${id}`);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, {
      method: 'DELETE',
      headers,
    });

    const result = await processApiResponse(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getNewsletterStats(): Promise<NewsletterStatsResponse> {
    const url = buildApiUrl(this.baseUrl, '/admin/newsletters/stats');
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse<NewsletterStatsResponse>(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getNewsletterHealth(): Promise<any> {
    const url = buildApiUrl(this.baseUrl, '/health/newsletter');
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  async getGenerationProgress(taskId: string): Promise<any> {
    const url = buildApiUrl(this.baseUrl, `/admin/tasks/${taskId}/progress`);
    const headers = createAuthHeaders(this.getToken());

    const response = await fetch(url, { headers });
    const result = await processApiResponse(response);

    if (result.error) {
      throw new SharedAPIError(result.status, result.error.message, result.error.code);
    }

    return result.data!;
  }

  // Placeholder methods for future implementation
  async bulkNewsletterOperation(_operation: any): Promise<any> {
    throw new Error('Bulk newsletter operations not yet implemented');
  }

  async searchNewsletters(_params: any): Promise<any> {
    throw new Error('Newsletter search not yet implemented');
  }

  async getNewsletterAnalytics(_period: string): Promise<any> {
    throw new Error('Newsletter analytics not yet implemented');
  }

  async exportNewsletter(_id: number, _format: string): Promise<any> {
    throw new Error('Newsletter export not yet implemented');
  }

  async validateNewsletter(_id: number): Promise<any> {
    throw new Error('Newsletter validation not yet implemented');
  }

  async getNewsletterPreview(_id: number): Promise<any> {
    throw new Error('Newsletter preview not yet implemented');
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  async testConnection(): Promise<boolean> {
    try {
      await this.getHealthCheck();
      return true;
    } catch {
      return false;
    }
  }

  // Get current authentication status
  isAuthenticated(): boolean {
    const token = this.getToken();
    return !!token && token.length > 0;
  }
}

// ============================================================================
// Default API Client Instance
// ============================================================================

// Token management (will be replaced by auth store)
let authToken: string | null = null;

export const getAuthToken = (): string | null => authToken;
export const setAuthToken = (token: string | null): void => {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

// Initialize token from localStorage
if (typeof window !== 'undefined') {
  authToken = localStorage.getItem('auth_token');
}

// Default API client instance
export const apiClient = new AdminAPIClient(config.apiUrl, getAuthToken);
