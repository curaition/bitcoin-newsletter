/**
 * Main Application Layout
 * 
 * Provides the core layout structure with sidebar navigation,
 * header, and main content area. Responsive design with mobile support.
 */

import { ReactNode, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppLayoutProps {
  children?: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background lg:flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 ease-in-out lg:relative lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main content area */}
      <div className="flex-1 lg:flex lg:flex-col">
        {/* Header */}
        <Header onMenuClick={() => setSidebarOpen(true)} />

        {/* Page content */}
        <main className="flex-1 p-6">
          {children || <Outlet />}
        </main>
      </div>
    </div>
  );
}

// ============================================================================
// Layout Hook for Sidebar State
// ============================================================================

export function useLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const toggleSidebar = () => setSidebarOpen(prev => !prev);
  const closeSidebar = () => setSidebarOpen(false);
  const openSidebar = () => setSidebarOpen(true);

  return {
    sidebarOpen,
    setSidebarOpen,
    toggleSidebar,
    closeSidebar,
    openSidebar,
  };
}
