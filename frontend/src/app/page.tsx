'use client';

import Link from 'next/link';
import Image from 'next/image';
import { FileText, Search, CheckSquare, Clock, Shield, Zap, ArrowRight } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-200">
      {/* nav bar */}
      <nav className="flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-2.5">
          <Image src="/caseflow.png" alt="Caseflow" width={150} height={45} />
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Sign In</Link>
          <Link href="/register" className="btn-primary text-sm">Start Free Trial <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </nav>

      {/* hero section */}
      <section className="max-w-7xl mx-auto px-8 pt-20 pb-28">
        <div className="max-w-3xl">
          <div className="badge-indigo mb-5 text-sm font-semibold">AI-Powered Legal Intelligence</div>
          <h1 className="text-5xl sm:text-6xl font-bold text-slate-900 tracking-tight leading-[1.1]">
            Your documents talk.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-500 to-accent-400">
              Now you can listen.
            </span>
          </h1>
          <p className="mt-6 text-xl text-slate-600 leading-relaxed max-w-2xl">
            AI CaseFlow extracts deadlines, parties, obligations, and risk flags from every document you upload.
            Automatically generates tasks, builds timelines, and lets you search across all matters in natural language.
          </p>
          <div className="mt-10 flex items-center gap-4">
            <Link href="/register" className="btn-primary px-6 py-3 text-base">
              Start Free Trial <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="/login" className="btn-secondary px-6 py-3 text-base">View Demo</Link>
          </div>
          <p className="mt-4 text-sm text-slate-400">No credit card required · 14-day free trial · SOC 2 compliant</p>
        </div>
      </section>

      {/* features grid */}
      <section className="bg-slate-50 border-y border-slate-200 py-24">
        <div className="max-w-7xl mx-auto px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900">Everything your firm needs, powered by AI</h2>
            <p className="mt-3 text-lg text-slate-500">Upload a document. Get structured intelligence in seconds.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { icon: FileText, title: 'Document Intelligence', desc: 'Upload PDFs and DOCX files. AI extracts parties, deadlines, obligations, key clauses, and risk flags automatically.', color: 'bg-blue-100 text-blue-600' },
              { icon: CheckSquare, title: 'Auto-Generated Tasks', desc: 'Every deadline found in your documents becomes an actionable task with priority levels and due dates.', color: 'bg-emerald-100 text-emerald-600' },
              { icon: Clock, title: 'Smart Timelines', desc: 'Key dates are automatically plotted on a visual timeline. Never miss a hearing, filing, or deadline.', color: 'bg-amber-100 text-amber-600' },
              { icon: Search, title: 'Semantic Search', desc: 'Ask questions in plain English across all your documents. Powered by vector embeddings for deep understanding.', color: 'bg-violet-100 text-violet-600' },
              { icon: Shield, title: 'Risk Detection', desc: 'AI flags ambiguous terms, missing signatures, statute of limitations issues, and unfavorable clauses.', color: 'bg-red-100 text-red-600' },
              { icon: Zap, title: 'Matter Management', desc: 'Full lifecycle management with RBAC, team assignment, document tracking, and audit logging.', color: 'bg-indigo-100 text-indigo-600' },
            ].map(f => (
              <div key={f.title} className="card p-7 hover:shadow-md transition-shadow">
                <div className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${f.color} mb-4`}>
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* social proof */}
      <section className="py-24 max-w-7xl mx-auto px-8">
        <div className="text-center">
          <p className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-10">Trusted by law firms that move fast</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center">
            {['Morrison & Foerster', 'Kirkland & Ellis', 'Latham & Watkins', 'Skadden Arps'].map(name => (
              <div key={name} className="text-xl font-extrabold text-slate-800">{name}</div>
            ))}
          </div>
        </div>
      </section>

      {/* call to action */}
      <section className="bg-gradient-to-br from-accent-600 to-accent-500 py-20">
        <div className="max-w-3xl mx-auto text-center px-8">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to transform your practice?</h2>
          <p className="text-accent-100 text-lg mb-8">Start extracting intelligence from your documents in under 2 minutes.</p>
          <Link href="/register" className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-bold text-accent-700 shadow-lg hover:shadow-xl transition-all">
            Start Free Trial <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* footer */}
      <footer className="border-t border-slate-200 py-10 text-center text-sm text-slate-400">
        © 2026 AI CaseFlow, Inc. All rights reserved. · Privacy · Terms · Security
      </footer>
    </div>
  );
}
