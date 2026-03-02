'use client';

import { useState } from 'react';
import { useMembers, useInviteMember } from '@/hooks/useApi';
import { Users, UserPlus, Shield, Briefcase, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

const roleStyles: Record<string, string> = { admin: 'badge-purple', lawyer: 'badge-blue', paralegal: 'badge-green' };
const roleIcons: Record<string, any> = { admin: Shield, lawyer: Briefcase, paralegal: FileText };

export default function MembersPage() {
  const { data: members, isLoading } = useMembers();
  const invite = useInviteMember();
  const [showInvite, setShowInvite] = useState(false);
  const [form, setForm] = useState({ email: '', full_name: '', role: 'lawyer' });

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await invite.mutateAsync(form);
      toast.success(`Invited ${form.email}`);
      setShowInvite(false);
      setForm({ email: '', full_name: '', role: 'lawyer' });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invite failed');
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">Team Members</h1>
          <p className="page-description">{members?.length || 0} members</p>
        </div>
        <button onClick={() => setShowInvite(!showInvite)} className="btn-primary">
          <UserPlus className="h-4 w-4" /> Invite Member
        </button>
      </div>

      {/* invite form */}
      {showInvite && (
        <form onSubmit={handleInvite} className="card p-6 mb-6 animate-fade-in">
          <h3 className="text-base font-bold text-slate-900 mb-4">Invite a Team Member</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Full Name</label>
              <input className="input" placeholder="Jane Smith" value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} required />
            </div>
            <div>
              <label className="label">Email</label>
              <input type="email" className="input" placeholder="jane@firm.com" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
            </div>
            <div>
              <label className="label">Role</label>
              <select className="input" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                <option value="admin">Admin</option>
                <option value="lawyer">Lawyer</option>
                <option value="paralegal">Paralegal</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <button type="button" onClick={() => setShowInvite(false)} className="btn-secondary text-sm">Cancel</button>
            <button type="submit" disabled={invite.isPending} className="btn-primary text-sm">
              {invite.isPending ? 'Sending...' : 'Send Invite'}
            </button>
          </div>
        </form>
      )}

      {/* member list */}
      <div className="card divide-y divide-slate-100">
        {isLoading ? (
          [1,2,3].map(i => <div key={i} className="h-16 animate-pulse bg-slate-50" />)
        ) : (
          members?.map(member => {
            const Icon = roleIcons[member.role] || Users;
            return (
              <div key={member.id} className="flex items-center gap-4 px-6 py-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700">
                  {member.user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-900">{member.user.full_name}</p>
                  <p className="text-xs text-slate-500">{member.user.email}</p>
                </div>
                <span className={roleStyles[member.role]}>
                  <Icon className="h-3 w-3 inline mr-1" />{member.role}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
