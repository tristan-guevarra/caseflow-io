'use client';

import { useDashboard } from '@/hooks/useApi';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Briefcase, CheckSquare, AlertTriangle, FileText, Clock, ArrowRight, Sparkles, TrendingUp } from 'lucide-react';
import { formatDistanceToNow, format, isPast, differenceInDays } from 'date-fns';

const priorityStyles: Record<string, string> = {
  urgent: 'badge-red',
  high: 'badge-yellow',
  medium: 'badge-blue',
  low: 'badge-gray',
};

const actionLabels: Record<string, string> = {
  'matter.created': 'created a matter',
  'document.uploaded': 'uploaded a document',
  'member.invited': 'invited a team member',
  'member.role_changed': 'changed a member role',
  'task.created': 'created a task',
  'org.created': 'created the organization',
};

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: stats, isLoading } = useDashboard();

  // loading skeleton
  if (isLoading || !stats) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-slate-200 rounded-lg animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="card p-6 h-28 animate-pulse bg-slate-100" />
          ))}
        </div>
      </div>
    );
  }

  const firstName = user?.full_name?.split(' ')[0] || 'there';

  return (
    <div className="space-y-8">
      {/* greeting */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {firstName}</h1>
        <p className="text-sm text-slate-500 mt-1">Here&apos;s what&apos;s happening across your matters today.</p>
      </div>

      {/* stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <Link href="/matters?status=active" className="stat-card hover:shadow-md transition-shadow group">
          <div className="flex items-center justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100">
              <Briefcase className="h-5 w-5 text-indigo-600" />
            </div>
            <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-indigo-500 transition-colors" />
          </div>
          <div className="mt-4">
            <p className="stat-value">{stats.active_matters}</p>
            <p className="stat-label">Active Matters</p>
          </div>
        </Link>

        <Link href="/tasks" className="stat-card hover:shadow-md transition-shadow group">
          <div className="flex items-center justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100">
              <CheckSquare className="h-5 w-5 text-amber-600" />
            </div>
            <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-amber-500 transition-colors" />
          </div>
          <div className="mt-4">
            <p className="stat-value">{stats.open_tasks}</p>
            <p className="stat-label">Open Tasks</p>
          </div>
        </Link>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            {stats.upcoming_deadlines > 0 && (
              <span className="badge-red animate-pulse-subtle">Action needed</span>
            )}
          </div>
          <div className="mt-4">
            <p className="stat-value">{stats.upcoming_deadlines}</p>
            <p className="stat-label">Deadlines This Week</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100">
              <FileText className="h-5 w-5 text-emerald-600" />
            </div>
            <Sparkles className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-4">
            <p className="stat-value">{stats.documents_processed}</p>
            <p className="stat-label">Documents Processed</p>
          </div>
        </div>
      </div>

      {/* two column layout for tasks and activity */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* upcoming deadlines */}
        <div className="lg:col-span-3 card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Clock className="h-4 w-4 text-slate-400" /> Upcoming Deadlines
            </h2>
            <Link href="/tasks" className="text-xs font-semibold text-indigo-600 hover:text-indigo-500">View all →</Link>
          </div>
          <div className="divide-y divide-slate-100">
            {stats.upcoming_tasks.length === 0 ? (
              <div className="px-6 py-10 text-center text-sm text-slate-400">No upcoming deadlines. You&apos;re all caught up!</div>
            ) : (
              stats.upcoming_tasks.slice(0, 6).map(task => {
                const daysUntil = task.due_date ? differenceInDays(new Date(task.due_date), new Date()) : null;
                const isOverdue = task.due_date ? isPast(new Date(task.due_date)) : false;
                return (
                  <div key={task.id} className="flex items-center gap-4 px-6 py-3.5 hover:bg-slate-50 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{task.title}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{task.matter_title || 'Unknown matter'}</p>
                    </div>
                    <span className={priorityStyles[task.priority]}>{task.priority}</span>
                    {task.due_date && (
                      <span className={`text-xs font-medium whitespace-nowrap ${isOverdue ? 'text-red-600' : daysUntil !== null && daysUntil <= 3 ? 'text-amber-600' : 'text-slate-500'}`}>
                        {isOverdue ? 'Overdue' : daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `${daysUntil}d left`}
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* recent activity feed */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-slate-400" /> Recent Activity
            </h2>
          </div>
          <div className="divide-y divide-slate-100">
            {stats.recent_activity.slice(0, 8).map(log => (
              <div key={log.id} className="px-6 py-3 hover:bg-slate-50 transition-colors">
                <p className="text-sm text-slate-700">
                  <span className="font-medium">{log.user_name || 'System'}</span>{' '}
                  {actionLabels[log.action] || log.action}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {log.details?.title || log.details?.filename || log.details?.email || ''}
                  {' · '}
                  {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
