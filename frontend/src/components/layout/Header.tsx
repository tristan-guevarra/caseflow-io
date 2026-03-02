'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Bell, ChevronRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

// build breadcrumb trail from the url path
function getBreadcrumbs(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];

  const labelMap: Record<string, string> = {
    dashboard: 'Dashboard',
    matters: 'Matters',
    tasks: 'Tasks',
    search: 'AI Search',
    notifications: 'Notifications',
    settings: 'Settings',
    members: 'Team',
    'audit-log': 'Audit Log',
    new: 'New Matter',
    profile: 'Profile',
    documents: 'Documents',
  };

  let path = '';
  for (const seg of segments) {
    path += `/${seg}`;
    const label = labelMap[seg] || (seg.length > 20 ? seg.slice(0, 8) + '...' : seg);
    crumbs.push({ label, href: path });
  }

  return crumbs;
}

export default function Header() {
  const pathname = usePathname();
  const { user } = useAuth();
  const crumbs = getBreadcrumbs(pathname);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 backdrop-blur-md px-6">
      {/* breadcrumbs */}
      <nav className="flex items-center gap-1.5 text-sm">
        {crumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-slate-300" />}
            {i === crumbs.length - 1 ? (
              <span className="font-semibold text-slate-900">{crumb.label}</span>
            ) : (
              <Link href={crumb.href} className="text-slate-500 hover:text-slate-700 transition-colors">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* notification bell and avatar */}
      <div className="flex items-center gap-3">
        <Link
          href="/notifications"
          className="relative rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            3
          </span>
        </Link>
        <Link href="/profile" className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-100 text-xs font-bold text-accent-700 hover:ring-2 hover:ring-accent-200 transition-all">
          {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase()}
        </Link>
      </div>
    </header>
  );
}
