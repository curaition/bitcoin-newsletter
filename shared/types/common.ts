/**
 * Common Types for Bitcoin Newsletter
 * 
 * Shared utility types used across frontend and backend
 */

// ============================================================================
// Environment Types
// ============================================================================

export type Environment = 'development' | 'staging' | 'production';

export interface AppConfig {
  environment: Environment;
  apiUrl: string;
  wsUrl?: string;
  version: string;
  debug: boolean;
}

// ============================================================================
// UI State Types
// ============================================================================

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastFetch?: Date;
}

export interface PaginationState {
  page: number;
  limit: number;
  total: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// ============================================================================
// Form Types
// ============================================================================

export interface FormField<T = string> {
  value: T;
  error?: string;
  touched: boolean;
  required?: boolean;
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

// ============================================================================
// Date/Time Types
// ============================================================================

export type DateRange = {
  start: Date | null;
  end: Date | null;
};

export type TimeUnit = 'minute' | 'hour' | 'day' | 'week' | 'month' | 'year';

// ============================================================================
// Search/Filter Types
// ============================================================================

export interface SearchState {
  query: string;
  filters: Record<string, any>;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterOption {
  key: string;
  label: string;
  type: 'text' | 'select' | 'date' | 'boolean';
  options?: { value: string; label: string }[];
}

// ============================================================================
// Notification Types
// ============================================================================

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number; // milliseconds
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// ============================================================================
// Theme Types
// ============================================================================

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeConfig {
  mode: ThemeMode;
  primaryColor?: string;
  accentColor?: string;
}

// ============================================================================
// Navigation Types
// ============================================================================

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  badge?: string | number;
  children?: NavItem[];
  disabled?: boolean;
  external?: boolean;
}

export interface Breadcrumb {
  label: string;
  path?: string;
  current?: boolean;
}

// ============================================================================
// Table Types
// ============================================================================

export interface TableColumn<T = any> {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: T) => React.ReactNode;
}

export interface TableState {
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  selectedRows: string[] | number[];
  expandedRows: string[] | number[];
}

// ============================================================================
// Chart/Analytics Types
// ============================================================================

export interface ChartDataPoint {
  x: string | number | Date;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartSeries {
  name: string;
  data: ChartDataPoint[];
  color?: string;
}

export type ChartType = 'line' | 'bar' | 'pie' | 'area' | 'scatter';

// ============================================================================
// File/Upload Types
// ============================================================================

export interface FileUpload {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  url?: string;
}

// ============================================================================
// Utility Types
// ============================================================================

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Make all properties of T optional except for specified keys
export type PartialExcept<T, K extends keyof T> = Partial<T> & Pick<T, K>;

// Extract the type of array elements
export type ArrayElement<T> = T extends (infer U)[] ? U : never;

// Create a union of all property names of T that are of type U
export type KeysOfType<T, U> = {
  [K in keyof T]: T[K] extends U ? K : never;
}[keyof T];

// ============================================================================
// Constants
// ============================================================================

export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

export const DEBOUNCE_DELAY = 300; // milliseconds
export const TOAST_DURATION = 5000; // milliseconds

export const DATE_FORMATS = {
  SHORT: 'MMM d, yyyy',
  LONG: 'MMMM d, yyyy',
  WITH_TIME: 'MMM d, yyyy h:mm a',
  ISO: "yyyy-MM-dd'T'HH:mm:ss.SSSxxx",
} as const;
