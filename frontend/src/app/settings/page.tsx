'use client';

import { useOrganization } from '@/hooks/useApi';
import { useAuth } from '@/contexts/AuthContext';
import { Building, Crown, HardDrive, Users } from 'lucide-react';

const tierLabels: Record<string, string> = { trial: 'Free Trial', starter: 'Starter', professional: 'Professional', enterprise: 'Enterprise' };
const tierStyles: Record<string, string> = { trial: 'badge-gray', starter: 'badge-blue', professional: 'badge-indigo', enterprise: 'badge-purple' };

export default function SettingsPage() {
  const { data: org, isLoading } = useOrganization();
  const { currentMembership } = useAuth();

  if (isLoading || !org) return <div className="h-64 bg-slate-100 rounded-xl animate-pulse" />;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">Organization Settings</h1>
        <p className="page-description">Manage your firm&apos;s account and subscription.</p>
      </div>

      <div className="space-y-6">
        {/* org info card */}
        <div className="card p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-indigo-100">
              <Building className="h-7 w-7 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">{org.name}</h2>
              <p className="text-sm text-slate-500">{org.slug}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50">
              <Crown className="h-5 w-5 text-indigo-500" />
              <div>
                <p className="text-sm font-semibold text-slate-900">{tierLabels[org.subscription_tier]}</p>
                <p className="text-xs text-slate-500">Current plan</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50">
              <Users className="h-5 w-5 text-emerald-500" />
              <div>
                <p className="text-sm font-semibold text-slate-900">Up to {org.max_users}</p>
                <p className="text-xs text-slate-500">Team members</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-50">
              <HardDrive className="h-5 w-5 text-amber-500" />
              <div>
                <p className="text-sm font-semibold text-slate-900">{(org.max_storage_mb / 1024).toFixed(0)} GB</p>
                <p className="text-xs text-slate-500">Storage limit</p>
              </div>
            </div>
          </div>
        </div>

        {/* upgrade cta */}
        <div className="card p-6">
          <h3 className="text-base font-bold text-slate-900 mb-4">Upgrade Plan</h3>
          <p className="text-sm text-slate-500 mb-4">Unlock more storage, users, and advanced features.</p>
          <button className="btn-primary">View Plans & Pricing</button>
        </div>
      </div>
    </div>
  );
}
