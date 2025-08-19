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
