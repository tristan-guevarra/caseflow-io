'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import { Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  // fill in demo credentials for quick testing
  const fillDemo = (role: string) => {
    const emails: Record<string, string> = {
      admin: 'sarah@demo-firm.com',
      lawyer: 'david@demo-firm.com',
      paralegal: 'maria@demo-firm.com',
    };
    setEmail(emails[role]);
    setPassword('Demo1234!');
  };

  return (
    <div className="min-h-screen flex">
      {/* login form side */}
      <div className="flex flex-1 flex-col justify-center px-8 py-12 lg:px-20">
        <div className="mx-auto w-full max-w-md">
          <Link href="/" className="inline-block mb-10">
            <Image src="/caseflow.png" alt="Caseflow" width={160} height={48} priority />
          </Link>

          <h1 className="text-2xl font-bold text-slate-900 mb-1">Welcome back</h1>
          <p className="text-sm text-slate-500 mb-8">Sign in to your CaseFlow account</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label">Email</label>
              <input type="email" className="input" placeholder="you@firm.com" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} className="input pr-10" placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* demo account buttons */}
          <div className="mt-6">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Quick Demo Access</p>
            <div className="flex gap-2">
              {[
                { role: 'admin', label: 'Admin', color: 'bg-violet-50 text-violet-700 ring-violet-200' },
                { role: 'lawyer', label: 'Lawyer', color: 'bg-blue-50 text-blue-700 ring-blue-200' },
                { role: 'paralegal', label: 'Paralegal', color: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
              ].map(d => (
                <button key={d.role} onClick={() => fillDemo(d.role)} className={`flex-1 rounded-lg py-2 text-xs font-semibold ring-1 ring-inset ${d.color} hover:opacity-80 transition-opacity`}>
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <p className="mt-8 text-center text-sm text-slate-500">
            Don&apos;t have an account? <Link href="/register" className="font-semibold text-accent-500 hover:text-accent-600">Create one</Link>
          </p>
        </div>
      </div>

      {/* testimonial side */}
      <div className="hidden lg:flex lg:flex-1 lg:items-center lg:justify-center bg-gradient-to-br from-accent-600 via-accent-500 to-accent-400 p-16">
        <div className="max-w-md text-white">
          <blockquote className="text-2xl font-medium leading-relaxed">
            &ldquo;CaseFlow cut our document review time by 70%. The AI extraction is incredibly accurate.&rdquo;
          </blockquote>
          <div className="mt-6 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">SC</div>
            <div>
              <p className="font-semibold">Sarah Chen</p>
              <p className="text-sm text-accent-100">Managing Partner, Chen & Park LLP</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
