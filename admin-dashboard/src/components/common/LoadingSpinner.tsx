/**
 * Loading Spinner Component
 * 
 * Reusable loading spinner with different sizes and variants.
 * Used for route transitions, API calls, and other async operations.
 */

import { cn } from '@/utils/cn';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'primary' | 'muted';
  className?: string;
  text?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12'
};

const variantClasses = {
  default: 'text-foreground',
  primary: 'text-primary',
  muted: 'text-muted-foreground'
};

export function LoadingSpinner({ 
  size = 'md', 
  variant = 'default', 
  className,
  text 
}: LoadingSpinnerProps) {
  return (
    <div className={cn("flex items-center justify-center", className)}>
      <div className="flex flex-col items-center space-y-2">
        <Loader2 
          className={cn(
            "animate-spin",
            sizeClasses[size],
            variantClasses[variant]
          )} 
        />
        {text && (
          <p className={cn(
            "text-sm",
            variantClasses[variant]
          )}>
            {text}
          </p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Page Loading Component
// ============================================================================

interface PageLoadingProps {
  message?: string;
}

export function PageLoading({ message = "Loading..." }: PageLoadingProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <LoadingSpinner 
        size="lg" 
        variant="primary" 
        text={message}
      />
    </div>
  );
}

// ============================================================================
// Full Screen Loading Component
// ============================================================================

interface FullScreenLoadingProps {
  message?: string;
}

export function FullScreenLoading({ message = "Loading..." }: FullScreenLoadingProps) {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-card border rounded-lg p-8 shadow-lg">
        <LoadingSpinner 
          size="xl" 
          variant="primary" 
          text={message}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Inline Loading Component
// ============================================================================

interface InlineLoadingProps {
  text?: string;
  className?: string;
}

export function InlineLoading({ text = "Loading...", className }: InlineLoadingProps) {
  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <LoadingSpinner size="sm" variant="muted" />
      <span className="text-sm text-muted-foreground">{text}</span>
    </div>
  );
}
