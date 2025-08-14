/**
 * Status Indicator Component
 * 
 * Visual status indicators for system health, connection status,
 * and other operational states.
 */

import { cn } from '@/utils/cn';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, XCircle, Clock } from 'lucide-react';

export type StatusType = 'online' | 'offline' | 'warning' | 'loading' | 'error';

interface StatusIndicatorProps {
  status: StatusType;
  text?: string;
  showIcon?: boolean;
  variant?: 'dot' | 'badge' | 'full';
  className?: string;
}

const statusConfig = {
  online: {
    color: 'bg-green-500',
    textColor: 'text-green-700',
    icon: CheckCircle,
    label: 'Online'
  },
  offline: {
    color: 'bg-gray-500',
    textColor: 'text-gray-700',
    icon: XCircle,
    label: 'Offline'
  },
  warning: {
    color: 'bg-yellow-500',
    textColor: 'text-yellow-700',
    icon: AlertCircle,
    label: 'Warning'
  },
  loading: {
    color: 'bg-blue-500',
    textColor: 'text-blue-700',
    icon: Clock,
    label: 'Loading'
  },
  error: {
    color: 'bg-red-500',
    textColor: 'text-red-700',
    icon: XCircle,
    label: 'Error'
  }
};

export function StatusIndicator({ 
  status, 
  text, 
  showIcon = false, 
  variant = 'dot',
  className 
}: StatusIndicatorProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  const displayText = text || config.label;

  if (variant === 'dot') {
    return (
      <div className={cn("flex items-center space-x-2", className)}>
        <div className={cn("h-2 w-2 rounded-full", config.color)} />
        {displayText && (
          <span className="text-sm text-muted-foreground">{displayText}</span>
        )}
      </div>
    );
  }

  if (variant === 'badge') {
    return (
      <Badge 
        variant="outline" 
        className={cn("flex items-center space-x-1", className)}
      >
        <div className={cn("h-2 w-2 rounded-full", config.color)} />
        <span>{displayText}</span>
      </Badge>
    );
  }

  // Full variant
  return (
    <div className={cn("flex items-center space-x-2", className)}>
      {showIcon && <Icon className={cn("h-4 w-4", config.textColor)} />}
      <div className={cn("h-2 w-2 rounded-full", config.color)} />
      <span className={cn("text-sm", config.textColor)}>{displayText}</span>
    </div>
  );
}

// ============================================================================
// Connection Status Component
// ============================================================================

interface ConnectionStatusProps {
  isConnected: boolean;
  className?: string;
}

export function ConnectionStatus({ isConnected, className }: ConnectionStatusProps) {
  return (
    <StatusIndicator
      status={isConnected ? 'online' : 'offline'}
      text={isConnected ? 'Connected' : 'Disconnected'}
      variant="badge"
      className={className}
    />
  );
}

// ============================================================================
// System Health Component
// ============================================================================

interface SystemHealthProps {
  health: 'healthy' | 'degraded' | 'down';
  className?: string;
}

export function SystemHealth({ health, className }: SystemHealthProps) {
  const statusMap: Record<string, StatusType> = {
    healthy: 'online',
    degraded: 'warning',
    down: 'error'
  };

  return (
    <StatusIndicator
      status={statusMap[health]}
      text={health.charAt(0).toUpperCase() + health.slice(1)}
      variant="badge"
      showIcon
      className={className}
    />
  );
}
