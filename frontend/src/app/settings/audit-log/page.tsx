'use client';

import { useState } from 'react';
import { useAuditLogs } from '@/hooks/useApi';
import { Shield, User, FileText, Briefcase, Users } from 'lucide-react';
import { format } from 'date-fns';

const resourceIcons: Record<string, any> = { matter: Briefcase, document: FileText, membership: Users, organization: Shield, task: FileText };

const actionLabels: Record<string, string> = {
  'matter.created': 'Created matter',
  'matter.updated': 'Updated matter',
  'document.uploaded': 'Uploaded document',
  'member.invited': 'Invited member',
  'member.role_changed': 'Changed member role',
  'task.created': 'Created task',
  'org.created': 'Organization created',
};

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAuditLogs({ page });

  return (
    <div className="max-w-4xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">Audit Log</h1>
        <p className="page-description">Complete history of all actions in your organization.</p>
      </div>

      {/* audit log table */}
      <div className="table-container">
        <table className="w-full">
          <thead><tr className="table-header">
            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Action</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Details</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">User</th>
            <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Time</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              [1,2,3,4,5].map(i => <tr key={i}><td colSpan={4} className="px-6 py-4"><div className="h-5 bg-slate-100 rounded animate-pulse" /></td></tr>)
            ) : (
              data?.items.map(log => {
                const Icon = resourceIcons[log.resource_type] || Shield;
                return (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100">
                          <Icon className="h-4 w-4 text-slate-500" />
                        </div>
                        <span className="text-sm font-medium text-slate-900">{actionLabels[log.action] || log.action}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-500 max-w-xs truncate">
                      {log.details?.title || log.details?.filename || log.details?.email || log.details?.new_role || '—'}
                    </td>
                    <td className="px-6 py-3.5 text-sm text-slate-600">{log.user_name || 'System'}</td>
                    <td className="px-6 py-3.5 text-xs text-slate-400">{format(new Date(log.created_at), 'MMM d, h:mm a')}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* pagination */}
      {data && data.total > 50 && (
        <div className="flex justify-between items-center mt-4 text-sm text-slate-500">
          <p>Page {page} · {data.total} entries</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs">Previous</button>
            <button onClick={() => setPage(p => p + 1)} disabled={page * 50 >= data.total} className="btn-secondary text-xs">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
