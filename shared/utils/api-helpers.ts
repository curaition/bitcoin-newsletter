/**
 * API Helper Utilities for Bitcoin Newsletter
 * 
 * Shared utilities for API interactions, URL building, and data formatting
 */

import type {
  ArticleListParams,
  APIResponse
} from '../types/api';

// ============================================================================
// URL Building Utilities
// ============================================================================

export function buildApiUrl(baseUrl: string, endpoint: string, params?: Record<string, any>): string {
  const url = new URL(endpoint, baseUrl);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          // Handle array parameters (e.g., categories)
          value.forEach(item => url.searchParams.append(key, String(item)));
        } else {
          url.searchParams.set(key, String(value));
        }
      }
    });
  }
  
  return url.toString();
}

export function buildArticleListUrl(baseUrl: string, params: ArticleListParams = {}): string {
  const cleanParams = {
    ...params,
    // Convert page to offset if needed
    offset: params.page ? (params.page - 1) * (params.limit || 20) : params.offset,
  };
  
  // Remove page since we're using offset
  delete cleanParams.page;
  
  return buildApiUrl(baseUrl, '/api/articles', cleanParams);
}

// ============================================================================
// Request Headers Utilities
// ============================================================================

export function createAuthHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  return headers;
}

export function createFormHeaders(token?: string | null): Record<string, string> {
  const headers: Record<string, string> = {};
  
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  // Don't set Content-Type for FormData - browser will set it with boundary
  return headers;
}

// ============================================================================
// Response Processing Utilities
// ============================================================================

export class APIError extends Error {
  public status: number;
  public code?: string;
  public details?: Record<string, any>;

  constructor(status: number, message: string, code?: string, details?: Record<string, any>) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.code = code;
    this.details = details;
  }

  static fromResponse(response: Response, data?: any): APIError {
    const message = data?.message || data?.detail || `HTTP ${response.status}: ${response.statusText}`;
    const code = data?.code || response.status.toString();
    const details = data?.details || {};
    
    return new APIError(response.status, message, code, details);
  }
}

export async function processApiResponse<T>(response: Response): Promise<APIResponse<T>> {
  const status = response.status;
  
  try {
    const data = await response.json();
    
    if (!response.ok) {
      const error = {
        message: data.message || data.detail || `HTTP ${status}: ${response.statusText}`,
        code: data.code || status.toString(),
        details: data.details || {},
        status,
      };
      
      return { error, status };
    }
    
    return { data, status };
  } catch (parseError) {
    const error = {
      message: response.ok ? 'Failed to parse response' : `HTTP ${status}: ${response.statusText}`,
      status,
    };
    
    return { error, status };
  }
}

// ============================================================================
// Pagination Utilities
// ============================================================================

export function calculatePagination(
  total: number, 
  page: number, 
  limit: number
): { offset: number; hasNext: boolean; hasPrevious: boolean } {
  const offset = (page - 1) * limit;
  const hasNext = offset + limit < total;
  const hasPrevious = page > 1;
  
  return { offset, hasNext, hasPrevious };
}

export function getPaginationInfo(
  total: number,
  offset: number,
  limit: number
): { page: number; totalPages: number; hasNext: boolean; hasPrevious: boolean } {
  const page = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);
  const hasNext = offset + limit < total;
  const hasPrevious = offset > 0;
  
  return { page, totalPages, hasNext, hasPrevious };
}

// ============================================================================
// Data Formatting Utilities
// ============================================================================

export function formatApiDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toISOString();
}

export function parseApiDate(dateString: string): Date {
  return new Date(dateString);
}

export function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

// ============================================================================
// Validation Utilities
// ============================================================================

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function sanitizeSearchQuery(query: string): string {
  return query
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML
    .substring(0, 200); // Limit length
}

// ============================================================================
// Retry Utilities
// ============================================================================

export interface RetryOptions {
  maxAttempts: number;
  delay: number;
  backoff?: 'linear' | 'exponential';
  shouldRetry?: (error: any) => boolean;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions
): Promise<T> {
  const { maxAttempts, delay, backoff = 'exponential', shouldRetry } = options;
  
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Don't retry if we shouldn't or if this is the last attempt
      if (attempt === maxAttempts || (shouldRetry && !shouldRetry(error))) {
        throw error;
      }
      
      // Calculate delay
      const currentDelay = backoff === 'exponential' 
        ? delay * Math.pow(2, attempt - 1)
        : delay * attempt;
      
      await new Promise(resolve => setTimeout(resolve, currentDelay));
    }
  }
  
  throw lastError;
}

// Default retry configuration for API calls
export const DEFAULT_RETRY_OPTIONS: RetryOptions = {
  maxAttempts: 3,
  delay: 1000,
  backoff: 'exponential',
  shouldRetry: (error) => {
    // Retry on network errors and 5xx server errors
    if (error instanceof APIError) {
      return error.status >= 500;
    }
    return true; // Retry on network errors
  },
};

// ============================================================================
// Cache Utilities
// ============================================================================

export function createCacheKey(prefix: string, params?: Record<string, any>): string {
  if (!params) return prefix;
  
  const sortedParams = Object.keys(params)
    .sort()
    .reduce((acc, key) => {
      const value = params[key];
      if (value !== undefined && value !== null) {
        acc[key] = Array.isArray(value) ? value.sort().join(',') : String(value);
      }
      return acc;
    }, {} as Record<string, string>);
  
  const paramString = new URLSearchParams(sortedParams).toString();
  return paramString ? `${prefix}?${paramString}` : prefix;
}
