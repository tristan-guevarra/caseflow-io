'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCreateMatter } from '@/hooks/useApi';
import toast from 'react-hot-toast';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NewMatterPage() {
  const router = useRouter();
  const createMatter = useCreateMatter();
  const [form, setForm] = useState({
    title: '', case_number: '', client_name: '', matter_type: 'litigation',
    jurisdiction: '', opposing_party: '', description: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const matter = await createMatter.mutateAsync(form);
      toast.success('Matter created');
      router.push(`/matters/${matter.id}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create matter');
    }
  };

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  return (
    <div className="max-w-2xl mx-auto">
      <Link href="/matters" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Matters
      </Link>

      <h1 className="page-title mb-8">Create New Matter</h1>

      {/* new matter form */}
      <form onSubmit={handleSubmit} className="card p-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="label">Matter Title *</label>
            <input className="input" placeholder="e.g., Acme Corp v. TechStart — Patent Infringement" value={form.title} onChange={update('title')} required />
          </div>
          <div>
            <label className="label">Case Number</label>
            <input className="input" placeholder="e.g., 2026-CV-04521" value={form.case_number} onChange={update('case_number')} />
          </div>
          <div>
            <label className="label">Client Name</label>
            <input className="input" placeholder="e.g., Acme Corporation" value={form.client_name} onChange={update('client_name')} />
          </div>
          <div>
            <label className="label">Matter Type *</label>
            <select className="input" value={form.matter_type} onChange={update('matter_type')}>
              <option value="litigation">Litigation</option>
              <option value="corporate">Corporate</option>
              <option value="real_estate">Real Estate</option>
              <option value="ip">Intellectual Property</option>
              <option value="employment">Employment</option>
              <option value="family">Family</option>
              <option value="criminal">Criminal</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="label">Jurisdiction</label>
            <input className="input" placeholder="e.g., Northern District of California" value={form.jurisdiction} onChange={update('jurisdiction')} />
          </div>
          <div className="md:col-span-2">
            <label className="label">Opposing Party</label>
            <input className="input" placeholder="e.g., TechStart Inc." value={form.opposing_party} onChange={update('opposing_party')} />
          </div>
          <div className="md:col-span-2">
            <label className="label">Description</label>
            <textarea className="input min-h-[120px]" placeholder="Brief description of the matter..." value={form.description} onChange={update('description')} />
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
          <Link href="/matters" className="btn-secondary">Cancel</Link>
          <button type="submit" disabled={createMatter.isPending} className="btn-primary">
            {createMatter.isPending ? 'Creating...' : 'Create Matter'}
          </button>
        </div>
      </form>
    </div>
  );
}
