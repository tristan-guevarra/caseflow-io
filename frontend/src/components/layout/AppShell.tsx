'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

const publicPaths = ['/', '/login', '/register', '/forgot-password'];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isPublicPage = publicPaths.includes(pathname);

  // redirect if not logged in, or redirect away from login if already logged in
  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isPublicPage) {
      router.push('/login');
    }
    if (!isLoading && isAuthenticated && (pathname === '/login' || pathname === '/register')) {
      router.push('/dashboard');
    }
  }, [isLoading, isAuthenticated, isPublicPage, pathname, router]);

  // loading spinner
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-200">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent-200 border-t-accent-500" />
          <p className="text-sm text-slate-500">Loading CaseFlow...</p>
        </div>
      </div>
    );
  }

  // public pages don't get the sidebar/header
  if (isPublicPage || !isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen bg-slate-200">
      <Sidebar />
      <div className="flex-1 ml-[260px]">
        <Header />
        <main className="p-6 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}
