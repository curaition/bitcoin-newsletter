/**
 * Breadcrumbs Navigation Component
 * 
 * Displays hierarchical navigation breadcrumbs based on current route.
 * Automatically generates breadcrumbs from the URL path.
 */

import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbsProps {
  className?: string;
}

interface BreadcrumbItem {
  label: string;
  href: string;
  isActive: boolean;
}

export function Breadcrumbs({ className }: BreadcrumbsProps) {
  const location = useLocation();

  // Generate breadcrumb items from current path
  const generateBreadcrumbs = (pathname: string): BreadcrumbItem[] => {
    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Always start with home/dashboard
    breadcrumbs.push({
      label: 'Dashboard',
      href: '/dashboard',
      isActive: pathname === '/dashboard'
    });

    // Build breadcrumbs from path segments
    let currentPath = '';
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === segments.length - 1;

      // Skip dashboard since we already added it
      if (segment === 'dashboard') return;

      // Generate label based on segment
      let label = segment;
      if (segment === 'articles') {
        label = 'Articles';
      } else if (segment === 'system') {
        label = 'System';
      } else if (segment === 'auth') {
        label = 'Authentication';
      } else if (segment === 'sign-in') {
        label = 'Sign In';
      } else if (segment.match(/^\d+$/)) {
        // If it's a numeric ID, show as "Article #ID"
        label = `Article #${segment}`;
      } else {
        // Capitalize first letter
        label = segment.charAt(0).toUpperCase() + segment.slice(1);
      }

      breadcrumbs.push({
        label,
        href: currentPath,
        isActive: isLast
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs(location.pathname);

  // Don't show breadcrumbs if we're only on dashboard
  if (breadcrumbs.length <= 1) {
    return null;
  }

  return (
    <nav className={cn("flex items-center space-x-1 text-sm text-muted-foreground", className)}>
      <Home className="h-3 w-3" />
      
      {breadcrumbs.map((item, index) => (
        <div key={item.href} className="flex items-center space-x-1">
          {index > 0 && <ChevronRight className="h-3 w-3" />}
          
          {item.isActive ? (
            <span className="font-medium text-foreground">
              {item.label}
            </span>
          ) : (
            <Link
              to={item.href}
              className="hover:text-foreground transition-colors"
            >
              {item.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  );
}
