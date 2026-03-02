'use client';

import { useAuth } from '@/contexts/AuthContext';
import { User, Mail, Calendar, Shield } from 'lucide-react';
import { format } from 'date-fns';

export default function ProfilePage() {
  const { user, currentMembership } = useAuth();

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">Profile</h1>
        <p className="page-description">Your account information.</p>
      </div>

      <div className="card p-8">
        {/* user avatar and name */}
        <div className="flex items-center gap-5 mb-8 pb-8 border-b border-slate-100">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-indigo-100 text-2xl font-bold text-indigo-700">
            {user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{user.full_name}</h2>
            <p className="text-sm text-slate-500">{user.email}</p>
            {currentMembership && <span className="badge-indigo mt-2 capitalize">{currentMembership.role}</span>}
          </div>
        </div>

        {/* account details */}
        <div className="space-y-5">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100"><Mail className="h-5 w-5 text-slate-500" /></div>
            <div>
              <p className="text-xs font-medium text-slate-400">Email</p>
              <p className="text-sm text-slate-900">{user.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100"><Shield className="h-5 w-5 text-slate-500" /></div>
            <div>
              <p className="text-xs font-medium text-slate-400">Role</p>
              <p className="text-sm text-slate-900 capitalize">{currentMembership?.role || 'Unknown'}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100"><Calendar className="h-5 w-5 text-slate-500" /></div>
            <div>
              <p className="text-xs font-medium text-slate-400">Member since</p>
              <p className="text-sm text-slate-900">{format(new Date(user.created_at), 'MMMM d, yyyy')}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
