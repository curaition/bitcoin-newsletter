/**
 * Sidebar Navigation Component
 * 
 * Main navigation sidebar with route links, user info, and system status.
 * Responsive design with mobile support.
 */

import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { useAuth } from '@/hooks/auth/useAuth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  LayoutDashboard, 
  FileText, 
  Settings, 
  LogOut, 
  X,
  Activity,
  User
} from 'lucide-react';

interface SidebarProps {
  onClose?: () => void;
}

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'System overview'
  },
  {
    name: 'Articles',
    href: '/articles',
    icon: FileText,
    description: 'Browse articles'
  },
  {
    name: 'System',
    href: '/system',
    icon: Settings,
    description: 'System controls'
  }
];

export function Sidebar({ onClose }: SidebarProps) {
  const location = useLocation();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <div className="flex h-full flex-col bg-card border-r border-border">
      {/* Header */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-border">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">Admin</span>
        </div>
        
        {/* Mobile close button */}
        {onClose && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="lg:hidden"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href || 
                          (item.href === '/articles' && location.pathname.startsWith('/articles'));
          
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={onClose}
              className={cn(
                "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              <div className="flex-1">
                <div>{item.name}</div>
                <div className="text-xs opacity-70">{item.description}</div>
              </div>
            </NavLink>
          );
        })}
      </nav>

      <Separator />

      {/* User section */}
      <div className="p-4 space-y-4">
        {user && (
          <div className="flex items-center space-x-3 p-2 rounded-lg bg-accent/50">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <User className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user.emailAddress || 'Admin User'}
              </p>
              <p className="text-xs text-muted-foreground">
                Administrator
              </p>
            </div>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={handleSignOut}
          className="w-full justify-start"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </Button>

        {/* Version info */}
        <div className="text-center">
          <Badge variant="secondary" className="text-xs">
            v1.0.0
          </Badge>
        </div>
      </div>
    </div>
  );
}
