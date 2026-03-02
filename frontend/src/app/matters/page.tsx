'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useMatters } from '@/hooks/useApi';
import { useAuth } from '@/contexts/AuthContext';
import { Plus, Search, Briefcase, Filter } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const statusStyles: Record<string, string> = {
  active: 'badge-green',
  pending: 'badge-yellow',
  closed: 'badge-gray',
  archived: 'badge-gray',
};

const typeLabels: Record<string, string> = {
  litigation: 'Litigation',
  corporate: 'Corporate',
  real_estate: 'Real Estate',
  ip: 'IP / Patent',
  employment: 'Employment',
  family: 'Family',
  criminal: 'Criminal',
  other: 'Other',
};

const typeColors: Record<string, string> = {
  litigation: 'badge-red',
  corporate: 'badge-blue',
  real_estate: 'badge-green',
  ip: 'badge-purple',
  employment: 'badge-yellow',
  family: 'badge-indigo',
  criminal: 'badge-red',
  other: 'badge-gray',
};

export default function MattersPage() {
  const { currentMembership } = useAuth();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useMatters({
    search: search || undefined,
    status: statusFilter || undefined,
    page,
  });

  const canCreate = currentMembership?.role !== 'paralegal';

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Matters</h1>
          <p className="page-description">Manage all your legal matters in one place.</p>
        </div>
        {canCreate && (
          <Link href="/matters/new" className="btn-primary">
            <Plus className="h-4 w-4" /> New Matter
          </Link>
        )}
      </div>

      {/* search and filter bar */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            className="input pl-10"
            placeholder="Search matters by title, client, or case number..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <select
          className="input w-44"
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="closed">Closed</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* matters table */}
      <div className="table-container">
        <table className="w-full">
          <thead>
            <tr className="table-header">
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Matter</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Client</th>
              <th className="px-6 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-6 py-4"><div className="h-5 bg-slate-100 rounded animate-pulse" /></td>
                </tr>
              ))
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-16 text-center">
                  <Briefcase className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm font-medium text-slate-500">No matters found</p>
                  <p className="text-xs text-slate-400 mt-1">Create your first matter to get started.</p>
                </td>
              </tr>
            ) : (
              data?.items.map(matter => (
                <tr key={matter.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <Link href={`/matters/${matter.id}`} className="block">
                      <p className="text-sm font-semibold text-slate-900 hover:text-indigo-600 transition-colors">{matter.title}</p>
                      {matter.case_number && <p className="text-xs text-slate-400 mt-0.5">{matter.case_number}</p>}
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <span className={typeColors[matter.matter_type] || 'badge-gray'}>{typeLabels[matter.matter_type]}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={statusStyles[matter.status]}>{matter.status}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600">{matter.client_name || '—'}</td>
                  <td className="px-6 py-4 text-xs text-slate-400">{formatDistanceToNow(new Date(matter.updated_at), { addSuffix: true })}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* pagination controls */}
      {data && data.total > data.page_size && (
        <div className="flex items-center justify-between mt-4 text-sm text-slate-500">
          <p>Showing {((page - 1) * data.page_size) + 1}–{Math.min(page * data.page_size, data.total)} of {data.total}</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn-secondary text-xs">Previous</button>
            <button onClick={() => setPage(p => p + 1)} disabled={page * data.page_size >= data.total} className="btn-secondary text-xs">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
