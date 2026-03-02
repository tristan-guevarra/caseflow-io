'use client';

import { useNotifications, useMarkNotificationRead, useMarkAllRead } from '@/hooks/useApi';
import Link from 'next/link';
import { Bell, FileText, Clock, CheckSquare, Settings, Check } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

// icons for different notification types
const typeIcons: Record<string, any> = {
  document_processed: FileText,
  deadline_alert: Clock,
  task_assigned: CheckSquare,
  system: Settings,
};

const typeStyles: Record<string, string> = {
  document_processed: 'bg-emerald-100 text-emerald-600',
  deadline_alert: 'bg-red-100 text-red-600',
  task_assigned: 'bg-blue-100 text-blue-600',
  system: 'bg-slate-100 text-slate-600',
};

export default function NotificationsPage() {
  const { data, isLoading } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-description">{data?.unread_count || 0} unread</p>
        </div>
        {data && data.unread_count > 0 && (
          <button onClick={() => markAll.mutate()} className="btn-secondary text-xs">
            <Check className="h-3.5 w-3.5" /> Mark all read
          </button>
        )}
      </div>

      {/* notification list */}
      <div className="card divide-y divide-slate-100">
        {isLoading ? (
          [1,2,3].map(i => <div key={i} className="h-16 animate-pulse bg-slate-50" />)
        ) : data?.items.length === 0 ? (
          <div className="p-12 text-center">
            <Bell className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500">No notifications yet</p>
          </div>
        ) : (
          data?.items.map(notif => {
            const Icon = typeIcons[notif.notification_type] || Bell;
            return (
              <div
                key={notif.id}
                className={`flex items-start gap-4 px-5 py-4 hover:bg-slate-50 transition-colors cursor-pointer ${!notif.is_read ? 'bg-indigo-50/30' : ''}`}
                onClick={() => { if (!notif.is_read) markRead.mutate(notif.id); }}
              >
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${typeStyles[notif.notification_type] || 'bg-slate-100 text-slate-600'}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${!notif.is_read ? 'font-semibold text-slate-900' : 'text-slate-700'}`}>{notif.title}</p>
                  {notif.message && <p className="text-xs text-slate-500 mt-0.5">{notif.message}</p>}
                  <p className="text-xs text-slate-400 mt-1">{formatDistanceToNow(new Date(notif.created_at), { addSuffix: true })}</p>
                </div>
                {!notif.is_read && <div className="h-2.5 w-2.5 rounded-full bg-indigo-500 shrink-0 mt-2" />}
                {notif.link && (
                  <Link href={notif.link} className="text-xs font-medium text-indigo-600 hover:text-indigo-500 shrink-0">View →</Link>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
