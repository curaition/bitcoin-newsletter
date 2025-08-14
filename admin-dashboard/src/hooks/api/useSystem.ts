/**
 * System API Hooks
 * 
 * React hooks for system status and health monitoring using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  SystemStatusResponse,
  TaskStatusResponse
} from '../../../../shared/types/api';
import { apiClient } from '@/services/api/client';
import { queryKeys, queryInvalidation } from '@/services/query/query-client';

// ============================================================================
// System Status Hook
// ============================================================================

export interface UseSystemStatusOptions {
  enabled?: boolean;
  refetchInterval?: number;
  refetchOnWindowFocus?: boolean;
}

export function useSystemStatus(options: UseSystemStatusOptions = {}) {
  const { 
    enabled = true, 
    refetchInterval = 30 * 1000, // 30 seconds
    refetchOnWindowFocus = false 
  } = options;
  
  return useQuery({
    queryKey: queryKeys.systemStatus(),
    queryFn: () => apiClient.getSystemStatus(),
    enabled,
    refetchInterval,
    refetchOnWindowFocus,
    select: (data: SystemStatusResponse) => ({
      timestamp: data.timestamp,
      service: data.service,
      environment: data.environment,
      api: data.api,
      database: data.database,
      celery: data.celery,
      // Computed overall health
      overallHealth: computeOverallHealth(data),
    }),
  });
}

// ============================================================================
// Health Check Hook
// ============================================================================

export function useHealthCheck(options: { enabled?: boolean; refetchInterval?: number } = {}) {
  const { enabled = true, refetchInterval = 60 * 1000 } = options; // 1 minute
  
  return useQuery({
    queryKey: queryKeys.healthCheck(),
    queryFn: () => apiClient.getHealthCheck(),
    enabled,
    refetchInterval,
    retry: 1, // Only retry once for health checks
    select: (data) => ({
      ...data,
      isHealthy: data.status === 'healthy',
      timestamp: new Date(data.timestamp),
    }),
  });
}

// ============================================================================
// Task Status Hook
// ============================================================================

export function useTaskStatus(taskId: string, options: { enabled?: boolean; refetchInterval?: number } = {}) {
  const { enabled = true, refetchInterval = 2000 } = options; // 2 seconds
  
  return useQuery({
    queryKey: queryKeys.adminTask(taskId),
    queryFn: () => apiClient.getTaskStatus(taskId),
    enabled: enabled && !!taskId,
    refetchInterval,
    select: (data: TaskStatusResponse) => ({
      ...data,
      isComplete: ['SUCCESS', 'FAILURE', 'REVOKED'].includes(data.status),
      isSuccess: data.status === 'SUCCESS',
      isFailure: data.status === 'FAILURE',
      isPending: ['PENDING', 'RETRY'].includes(data.status),
    }),
  });
}

// ============================================================================
// Connection Test Hook
// ============================================================================

export function useConnectionTest() {
  return useMutation({
    mutationFn: () => apiClient.testConnection(),
    onSuccess: (isConnected) => {
      console.log('Connection test result:', isConnected);
    },
    onError: (error) => {
      console.error('Connection test failed:', error);
    },
  });
}

// ============================================================================
// System Monitoring Hook (Combined)
// ============================================================================

export function useSystemMonitoring(options: { enabled?: boolean } = {}) {
  const { enabled = true } = options;
  
  const systemStatus = useSystemStatus({ 
    enabled,
    refetchInterval: 30 * 1000, // 30 seconds
  });
  
  const healthCheck = useHealthCheck({ 
    enabled,
    refetchInterval: 60 * 1000, // 1 minute
  });
  
  return {
    systemStatus,
    healthCheck,
    
    // Computed states
    isLoading: systemStatus.isLoading || healthCheck.isLoading,
    isError: systemStatus.isError || healthCheck.isError,
    error: systemStatus.error || healthCheck.error,
    
    // Combined health status
    overallHealth: computeCombinedHealth(systemStatus.data, healthCheck.data),
    
    // Refresh all
    refetch: () => {
      systemStatus.refetch();
      healthCheck.refetch();
    },
  };
}

// ============================================================================
// Real-time System Updates Hook
// ============================================================================

export function useSystemUpdates() {
  const queryClient = useQueryClient();
  
  // Manually trigger system status refresh
  const refreshSystemStatus = () => {
    queryInvalidation.system();
  };
  
  // Check if system is currently healthy
  const isSystemHealthy = () => {
    const systemStatus = queryClient.getQueryData(queryKeys.systemStatus()) as SystemStatusResponse | undefined;
    const healthCheck = queryClient.getQueryData(queryKeys.healthCheck()) as any;
    
    return computeCombinedHealth(systemStatus, healthCheck) === 'healthy';
  };
  
  return {
    refreshSystemStatus,
    isSystemHealthy,
    
    // Invalidate specific parts
    refreshDatabase: () => queryInvalidation.system(),
    refreshCelery: () => queryInvalidation.system(),
    refreshAPI: () => queryInvalidation.system(),
  };
}

// ============================================================================
// Utility Functions
// ============================================================================

function computeOverallHealth(status: SystemStatusResponse): 'healthy' | 'warning' | 'error' | 'unknown' {
  const components = [status.api, status.database, status.celery].filter(Boolean);
  
  if (components.length === 0) return 'unknown';
  
  const hasError = components.some(c => c?.status === 'error');
  const hasWarning = components.some(c => c?.status === 'warning');
  
  if (hasError) return 'error';
  if (hasWarning) return 'warning';
  
  return 'healthy';
}

function computeCombinedHealth(
  systemStatus?: SystemStatusResponse | null, 
  healthCheck?: { status: string } | null
): 'healthy' | 'warning' | 'error' | 'unknown' {
  if (!systemStatus && !healthCheck) return 'unknown';
  
  // If health check fails, system is unhealthy
  if (healthCheck && healthCheck.status !== 'healthy') {
    return 'error';
  }
  
  // Use system status if available
  if (systemStatus) {
    return computeOverallHealth(systemStatus);
  }
  
  // Fallback to health check
  return healthCheck?.status === 'healthy' ? 'healthy' : 'unknown';
}

// ============================================================================
// System Metrics Hook (Future Enhancement)
// ============================================================================

export function useSystemMetrics(options: { enabled?: boolean } = {}) {
  const { enabled = false } = options; // Disabled by default
  
  return useQuery({
    queryKey: [...queryKeys.system, 'metrics'],
    queryFn: async () => {
      // This would call a metrics endpoint when available
      // For now, return mock data
      return {
        cpu: 45,
        memory: 67,
        disk: 23,
        network: 12,
      };
    },
    enabled,
    refetchInterval: 10 * 1000, // 10 seconds
  });
}
