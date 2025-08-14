/**
 * Header Component
 * 
 * Top navigation bar with breadcrumbs, user menu, and mobile menu toggle.
 * Responsive design with mobile hamburger menu.
 */

import { useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/auth/useAuth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Breadcrumbs } from './Breadcrumbs';
import { Menu, Bell, User } from 'lucide-react';

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const location = useLocation();
  const { user } = useAuth();

  // Get page title from current route
  const getPageTitle = (pathname: string): string => {
    if (pathname === '/dashboard') return 'Dashboard';
    if (pathname === '/articles') return 'Articles';
    if (pathname.startsWith('/articles/')) return 'Article Details';
    if (pathname === '/system') return 'System';
    if (pathname === '/auth/sign-in') return 'Sign In';
    return 'Admin';
  };

  const pageTitle = getPageTitle(location.pathname);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      {/* Left section */}
      <div className="flex items-center space-x-4">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="lg:hidden"
        >
          <Menu className="h-4 w-4" />
        </Button>

        {/* Page title and breadcrumbs */}
        <div className="flex items-center space-x-6">
          <h1 className="text-lg font-semibold">{pageTitle}</h1>
          <div className="hidden sm:block">
            <Breadcrumbs />
          </div>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center space-x-4">
        {/* Environment badge */}
        <Badge variant="outline" className="hidden sm:inline-flex">
          Development
        </Badge>

        {/* Notifications (placeholder) */}
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-4 w-4" />
          {/* Notification dot */}
          <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-red-500" />
        </Button>

        {/* User menu */}
        <div className="flex items-center space-x-2">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium">
              {user?.emailAddress || 'Admin User'}
            </p>
            <p className="text-xs text-muted-foreground">
              Administrator
            </p>
          </div>
          <Button variant="ghost" size="sm" className="relative h-8 w-8 rounded-full">
            <User className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
