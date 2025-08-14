/**
 * Type Guards for Bitcoin Newsletter
 * 
 * Runtime type checking utilities for API responses and data validation
 */

import type { 
  Article, 
  Publisher, 
  Category, 
  SystemStatusResponse,
  APIResponse,
  ArticleStatus,
  ArticleSentiment,
  User
} from '../types/api';

// ============================================================================
// Basic Type Guards
// ============================================================================

export function isString(value: unknown): value is string {
  return typeof value === 'string';
}

export function isNumber(value: unknown): value is number {
  return typeof value === 'number' && !isNaN(value);
}

export function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean';
}

export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function isArray<T>(value: unknown, itemGuard?: (item: unknown) => item is T): value is T[] {
  if (!Array.isArray(value)) return false;
  if (!itemGuard) return true;
  return value.every(itemGuard);
}

export function isNullOrUndefined(value: unknown): value is null | undefined {
  return value === null || value === undefined;
}

export function isValidDate(value: unknown): value is string {
  if (!isString(value)) return false;
  const date = new Date(value);
  return !isNaN(date.getTime());
}

// ============================================================================
// Enum Type Guards
// ============================================================================

export function isArticleStatus(value: unknown): value is ArticleStatus {
  return isString(value) && ['ACTIVE', 'INACTIVE', 'DELETED'].includes(value);
}

export function isArticleSentiment(value: unknown): value is ArticleSentiment {
  return isString(value) && ['POSITIVE', 'NEGATIVE', 'NEUTRAL'].includes(value);
}

// ============================================================================
// Domain Model Type Guards
// ============================================================================

export function isPublisher(value: unknown): value is Publisher {
  if (!isObject(value)) return false;
  
  const obj = value as Record<string, unknown>;
  
  return (
    isNumber(obj.id) &&
    isNumber(obj.source_id) &&
    isString(obj.name) &&
    isString(obj.url) &&
    isString(obj.rss_url) &&
    isString(obj.language) &&
    isArticleStatus(obj.status) &&
    isValidDate(obj.created_at) &&
    isValidDate(obj.updated_at)
  );
}

export function isCategory(value: unknown): value is Category {
  if (!isObject(value)) return false;
  
  const obj = value as Record<string, unknown>;
  
  return (
    isNumber(obj.id) &&
    isNumber(obj.category_id) &&
    isString(obj.name) &&
    isString(obj.category) &&
    isValidDate(obj.created_at) &&
    isValidDate(obj.updated_at)
  );
}

export function isArticle(value: unknown): value is Article {
  if (!isObject(value)) return false;
  
  const obj = value as Record<string, unknown>;
  
  return (
    isNumber(obj.id) &&
    isString(obj.guid) &&
    isString(obj.title) &&
    isString(obj.url) &&
    (obj.body === null || isString(obj.body)) &&
    (obj.summary === null || isString(obj.summary)) &&
    (obj.authors === null || isString(obj.authors)) &&
    isValidDate(obj.published_on) &&
    (obj.language === null || isString(obj.language)) &&
    (obj.keywords === null || isString(obj.keywords)) &&
    (obj.sentiment === null || isArticleSentiment(obj.sentiment)) &&
    isArticleStatus(obj.status) &&
    (obj.publisher_id === null || isNumber(obj.publisher_id)) &&
    (obj.source_id === null || isNumber(obj.source_id)) &&
    isValidDate(obj.created_at) &&
    isValidDate(obj.updated_at)
  );
}

export function isUser(value: unknown): value is User {
  if (!isObject(value)) return false;
  
  const obj = value as Record<string, unknown>;
  
  return (
    isString(obj.id) &&
    isString(obj.emailAddress) &&
    (obj.firstName === undefined || isString(obj.firstName)) &&
    (obj.lastName === undefined || isString(obj.lastName)) &&
    (obj.imageUrl === undefined || isString(obj.imageUrl)) &&
    (obj.username === undefined || isString(obj.username))
  );
}

// ============================================================================
// API Response Type Guards
// ============================================================================

export function isAPIResponse<T>(
  value: unknown,
  dataGuard?: (data: unknown) => data is T
): value is APIResponse<T> {
  if (!isObject(value)) return false;
  
  const obj = value as Record<string, unknown>;
  
  // Must have status
  if (!isNumber(obj.status)) return false;
  
  // If data exists, validate it
  if (obj.data !== undefined && dataGuard && !dataGuard(obj.data)) {
    return false;
  }
  
  // If error exists, validate it
  if (obj.error !== undefined) {
    if (!isObject(obj.error)) return false;
    const error = obj.error as Record<string, unknown>;
    if (!isString(error.message)) return false;
  }
  
  return true;
}

export function isSystemStatusResponse(value: unknown): value is SystemStatusResponse {
  if (!isObject(value)) return false;
  
  const obj = value as Record<string, unknown>;
  
  return (
    isValidDate(obj.timestamp) &&
    isString(obj.service) &&
    isString(obj.environment)
  );
}

// ============================================================================
// Array Type Guards
// ============================================================================

export function isArticleArray(value: unknown): value is Article[] {
  return isArray(value, isArticle);
}

export function isPublisherArray(value: unknown): value is Publisher[] {
  return isArray(value, isPublisher);
}

export function isCategoryArray(value: unknown): value is Category[] {
  return isArray(value, isCategory);
}

// ============================================================================
// Utility Functions
// ============================================================================

export function assertIsArticle(value: unknown): asserts value is Article {
  if (!isArticle(value)) {
    throw new Error('Expected Article object');
  }
}

export function assertIsUser(value: unknown): asserts value is User {
  if (!isUser(value)) {
    throw new Error('Expected User object');
  }
}

export function safeParseJSON<T>(
  json: string,
  guard: (value: unknown) => value is T
): T | null {
  try {
    const parsed = JSON.parse(json);
    return guard(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

// ============================================================================
// Validation Helpers
// ============================================================================

export function validateArticleForDisplay(article: unknown): article is Article {
  if (!isArticle(article)) return false;
  
  // Additional validation for display purposes
  return (
    article.title.trim().length > 0 &&
    article.url.startsWith('http') &&
    article.published_on !== null
  );
}

export function validateUserForAuth(user: unknown): user is User {
  if (!isUser(user)) return false;
  
  // Additional validation for authentication
  return (
    user.emailAddress.includes('@') &&
    user.id.length > 0
  );
}
