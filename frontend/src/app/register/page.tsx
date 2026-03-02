'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({ fullName: '', email: '', orgName: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form.email, form.password, form.fullName, form.orgName);
      toast.success('Account created!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-200 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block mb-6">
            <Image src="/caseflow.png" alt="Caseflow" width={160} height={48} priority />
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
          <p className="text-sm text-slate-500 mt-1">14-day free trial. No credit card required.</p>
        </div>

        {/* registration form */}
        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Full Name</label>
              <input className="input" placeholder="Jane Smith" value={form.fullName} onChange={e => setForm(f => ({ ...f, fullName: e.target.value }))} required />
            </div>
            <div>
              <label className="label">Work Email</label>
              <input type="email" className="input" placeholder="you@firm.com" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
            </div>
            <div>
              <label className="label">Firm / Organization Name</label>
              <input className="input" placeholder="Smith & Associates LLP" value={form.orgName} onChange={e => setForm(f => ({ ...f, orgName: e.target.value }))} required />
            </div>
            <div>
              <label className="label">Password</label>
              <input type="password" className="input" placeholder="Min 8 chars, 1 upper, 1 digit, 1 symbol" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required minLength={8} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account? <Link href="/login" className="font-semibold text-accent-500 hover:text-accent-600">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
