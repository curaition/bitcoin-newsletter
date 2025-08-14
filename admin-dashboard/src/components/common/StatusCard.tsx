/**
 * StatusCard Component
 * 
 * Reusable component for displaying system status information
 * with consistent styling and loading states.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, AlertCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface StatusCardProps {
  title: string;
  status?: 'healthy' | 'warning' | 'error' | 'unknown';
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  isLoading?: boolean;
  className?: string;
}

export function StatusCard({
  title,
  status = 'unknown',
  value,
  description,
  icon,
  isLoading = false,
  className
}: StatusCardProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <HelpCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = () => {
    const variants = {
      healthy: 'secondary',
      warning: 'outline',
      error: 'destructive',
      unknown: 'outline'
    } as const;

    const colors = {
      healthy: 'text-green-600 bg-green-50 border-green-200',
      warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      error: 'text-red-600 bg-red-50 border-red-200',
      unknown: 'text-gray-600 bg-gray-50 border-gray-200'
    };

    return (
      <Badge 
        variant={variants[status]} 
        className={cn('text-xs capitalize', colors[status])}
      >
        {status}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {icon && <div className="text-muted-foreground">{icon}</div>}
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="h-8 w-20 bg-muted animate-pulse rounded" />
            <div className="h-4 w-16 bg-muted animate-pulse rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="text-2xl font-bold">{value}</div>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className="flex flex-col items-end space-y-2">
            {getStatusIcon()}
            {getStatusBadge()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Utility function to determine status from various inputs
export function determineStatus(
  value: any,
  healthyCondition?: (value: any) => boolean
): 'healthy' | 'warning' | 'error' | 'unknown' {
  if (value === undefined || value === null) return 'unknown';
  
  if (typeof value === 'string') {
    const lowerValue = value.toLowerCase();
    if (['healthy', 'active', 'connected', 'online'].includes(lowerValue)) return 'healthy';
    if (['warning', 'degraded'].includes(lowerValue)) return 'warning';
    if (['error', 'failed', 'offline', 'disconnected'].includes(lowerValue)) return 'error';
  }
  
  if (typeof value === 'boolean') {
    return value ? 'healthy' : 'error';
  }
  
  if (healthyCondition) {
    return healthyCondition(value) ? 'healthy' : 'warning';
  }
  
  return 'unknown';
}
