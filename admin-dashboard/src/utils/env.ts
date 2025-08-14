import type { AppConfig, Environment } from '../../../shared/types/common';

// Environment variable validation and defaults
function getEnvVar(key: string, defaultValue?: string): string {
  const value = import.meta.env[key];
  if (!value && !defaultValue) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value || defaultValue!;
}

function getOptionalEnvVar(key: string, defaultValue?: string): string | undefined {
  return import.meta.env[key] || defaultValue;
}

// App configuration
export const config: AppConfig = {
  environment: (getOptionalEnvVar('VITE_APP_ENV', 'development') as Environment),
  apiUrl: getEnvVar('VITE_API_URL', 'http://localhost:8000'),
  wsUrl: getOptionalEnvVar('VITE_WS_URL'),
  version: getOptionalEnvVar('VITE_APP_VERSION', '1.0.0') || '1.0.0',
  debug: import.meta.env.DEV,
};

// Validation
if (!['development', 'staging', 'production'].includes(config.environment)) {
  throw new Error(`Invalid environment: ${config.environment}`);
}

// Helper functions
export const isDevelopment = config.environment === 'development';
export const isProduction = config.environment === 'production';
export const isStaging = config.environment === 'staging';

// API endpoints
export const API_ENDPOINTS = {
  // Authentication
  login: '/auth/login',
  logout: '/auth/logout',
  refresh: '/auth/refresh',
  
  // Articles
  articles: '/api/articles',
  article: (id: number) => `/api/articles/${id}`,

  // Publishers
  publishers: '/api/publishers',

  // Publishers
  publishers: '/api/publishers',
  
  // Admin
  adminStatus: '/admin/status',
  adminIngest: '/admin/ingest',
  adminTasks: '/admin/tasks',
  
  // System
  health: '/health',
  metrics: '/metrics',
} as const;

// Build full API URLs
export function buildApiUrl(endpoint: string): string {
  return `${config.apiUrl}${endpoint}`;
}

// Log configuration in development
if (isDevelopment) {
  console.log('🔧 App Configuration:', {
    environment: config.environment,
    apiUrl: config.apiUrl,
    version: config.version,
    debug: config.debug,
  });
}
