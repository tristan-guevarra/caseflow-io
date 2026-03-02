'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard,
  Briefcase,
  CheckSquare,
  Search,
  Bell,
  Settings,
  Users,
  Shield,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// main nav links
const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, minRole: 'paralegal' },
  { href: '/matters', label: 'Matters', icon: Briefcase, minRole: 'paralegal' },
  { href: '/tasks', label: 'Tasks', icon: CheckSquare, minRole: 'paralegal' },
  { href: '/search', label: 'AI Search', icon: Search, minRole: 'lawyer' },
  { href: '/notifications', label: 'Notifications', icon: Bell, minRole: 'paralegal' },
];

// admin-only links
const adminItems = [
  { href: '/settings', label: 'Settings', icon: Settings, minRole: 'admin' },
  { href: '/settings/members', label: 'Team', icon: Users, minRole: 'admin' },
  { href: '/settings/audit-log', label: 'Audit Log', icon: Shield, minRole: 'admin' },
];

const roleHierarchy: Record<string, number> = { admin: 3, lawyer: 2, paralegal: 1 };

export default function Sidebar() {
  const pathname = usePathname();
  const { user, currentMembership, logout } = useAuth();

  const role = currentMembership?.role || 'paralegal';
  const userLevel = roleHierarchy[role] || 0;

  const canAccess = (minRole: string) => userLevel >= (roleHierarchy[minRole] || 99);

  const NavLink = ({ href, label, icon: Icon }: { href: string; label: string; icon: any }) => {
    const isActive = pathname === href || (href !== '/dashboard' && pathname.startsWith(href));
    return (
      <Link
        href={href}
        className={cn(
          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
          isActive
            ? 'bg-accent-50 text-accent-700'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
        )}
      >
        <Icon className={cn('h-[18px] w-[18px]', isActive ? 'text-accent-500' : 'text-slate-400')} />
        {label}
      </Link>
    );
  };

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-[260px] flex-col border-r border-slate-200 bg-white">
      {/* logo */}
      <div className="flex h-16 items-center border-b border-slate-200 px-5">
        <Link href="/dashboard">
          <Image src="/caseflow.png" alt="Caseflow" width={130} height={40} />
        </Link>
      </div>

      {/* sidebar nav links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.filter(i => canAccess(i.minRole)).map(item => (
          <NavLink key={item.href} {...item} />
        ))}

        {canAccess('admin') && (
          <>
            <div className="my-4 border-t border-slate-200" />
            <p className="px-3 mb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Administration</p>
            {adminItems.filter(i => canAccess(i.minRole)).map(item => (
              <NavLink key={item.href} {...item} />
            ))}
          </>
        )}
      </nav>

      {/* user info and logout */}
      <div className="border-t border-slate-200 p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent-100 text-sm font-bold text-accent-700">
            {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-900 truncate">{user?.full_name}</p>
            <p className="text-xs text-slate-500 capitalize">{role}</p>
          </div>
          <button onClick={logout} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
