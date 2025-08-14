/**
 * Shared API Types for Bitcoin Newsletter
 * 
 * These types match the backend Pydantic models and database schemas.
 * Keep in sync with backend models in src/crypto_newsletter/shared/models/
 */

// ============================================================================
// Base Types
// ============================================================================

export interface TimestampMixin {
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}

export type ArticleStatus = 'ACTIVE' | 'INACTIVE' | 'DELETED';
export type ArticleSentiment = 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';

// ============================================================================
// Core Domain Models
// ============================================================================

export interface Publisher extends TimestampMixin {
  id: number;
  source_id: number;
  name: string;
  url: string;
  rss_url: string;
  language: string;
  status: ArticleStatus;
}

export interface Category extends TimestampMixin {
  id: number;
  category_id: number;
  name: string;
  category: string;
}

export interface Article extends TimestampMixin {
  id: number;
  guid: string;
  title: string;
  url: string;
  body: string | null;
  summary: string | null;
  authors: string | null;
  published_on: string; // ISO 8601 datetime
  language: string | null;
  keywords: string | null;
  sentiment: ArticleSentiment | null;
  status: ArticleStatus;
  
  // Foreign key relationships
  publisher_id: number | null;
  source_id: number | null;
  
  // Populated relationships (when included)
  publisher?: Publisher;
  article_categories?: ArticleCategory[];
}

export interface ArticleCategory extends TimestampMixin {
  id: number;
  article_id: number;
  category_id: number;
  
  // Populated relationships
  article?: Article;
  category?: Category;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface PaginationResponse {
  total: number;
  page: number;
  limit: number;
  offset: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface ArticleListParams extends PaginationParams {
  search?: string;
  publisher?: string;
  status?: ArticleStatus;
  start_date?: string; // ISO 8601 date
  end_date?: string;   // ISO 8601 date
  orderBy?: 'created_at' | 'published_on' | 'title';
  order?: 'asc' | 'desc';
}

// Current API returns simple array, not paginated response
export interface ArticleListResponse extends Array<Article> {}

// Future paginated response structure
export interface PaginatedArticleListResponse {
  data: Article[];
  pagination: PaginationResponse;
}

export interface ArticleDetailResponse {
  data: Article;
}

// ============================================================================
// System Status Types
// ============================================================================

export interface SystemHealthStatus {
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  message?: string;
  details?: Record<string, any>;
}

export interface DatabaseStatus extends SystemHealthStatus {
  total_articles?: number;
  recent_articles_24h?: number;
  top_publishers?: Array<{
    publisher: string;
    count: number;
  }>;
  top_categories?: Array<{
    category: string;
    count: number;
  }>;
  last_updated?: string; // ISO 8601 datetime
  // Legacy fields for backward compatibility
  connection_count?: number;
  articles_count?: number;
  publishers_count?: number;
  last_article_ingested?: string; // ISO 8601 datetime
}

export interface CeleryStatus extends SystemHealthStatus {
  active_tasks?: {
    active: number | null;
    scheduled: number | null;
    reserved: number | null;
  };
  workers?: {
    status: string;
    message: string;
    workers: number;
  };
  workers_online?: number;
  last_run?: string; // ISO 8601 datetime
  queue_lengths?: Record<string, number>;
}

export interface APIStatus extends SystemHealthStatus {
  version?: string;
  uptime?: string;
  environment?: string;
}

export interface SystemStatusResponse {
  timestamp: string; // ISO 8601 datetime
  service: string;
  environment: string;
  api?: APIStatus;
  database?: DatabaseStatus;
  celery?: CeleryStatus;
}

// ============================================================================
// Admin Operations Types
// ============================================================================

export interface ManualIngestRequest {
  limit?: number;
  hours_back?: number;
  categories?: string[];
}

export interface IngestionResult {
  success: boolean;
  articles_fetched?: number;
  articles_processed?: number;
  duplicates_skipped?: number;
  processing_time_seconds?: number;
  success_rate?: number;
  error?: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILURE' | 'RETRY' | 'REVOKED';
  result?: any;
  date_done?: string; // ISO 8601 datetime
  traceback?: string;
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface LoginRequest {
  emailAddress: string; // Clerk-compatible naming
  password: string;
}

export interface User {
  id: string;
  emailAddress: string; // Clerk-compatible naming
  firstName?: string;
  lastName?: string;
  imageUrl?: string;
  username?: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

// ============================================================================
// Error Types
// ============================================================================

export interface APIError {
  message: string;
  code?: string;
  details?: Record<string, any>;
  status?: number;
}

export interface APIResponse<T = any> {
  data?: T;
  error?: APIError;
  status: number;
}

// ============================================================================
// Utility Types
// ============================================================================

export type SortOrder = 'asc' | 'desc';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

// Publisher options for dropdowns
export type PublisherOption = SelectOption;

// Status options for filters
export const ARTICLE_STATUS_OPTIONS: SelectOption[] = [
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'DELETED', label: 'Deleted' },
];

export const ARTICLE_SENTIMENT_OPTIONS: SelectOption[] = [
  { value: 'POSITIVE', label: 'Positive' },
  { value: 'NEGATIVE', label: 'Negative' },
  { value: 'NEUTRAL', label: 'Neutral' },
];
