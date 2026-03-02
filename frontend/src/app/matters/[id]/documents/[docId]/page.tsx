'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useDocument, useReprocessDocument } from '@/hooks/useApi';
import { ArrowLeft, FileText, Users, Clock, AlertTriangle, BookOpen, ShieldAlert, Sparkles, RefreshCw, CheckCircle, Hash } from 'lucide-react';
import { format } from 'date-fns';

const extractionTabs = [
  { id: 'summary', label: 'Summary', icon: BookOpen },
  { id: 'parties', label: 'Parties', icon: Users },
  { id: 'deadlines', label: 'Deadlines', icon: Clock },
  { id: 'obligations', label: 'Obligations', icon: CheckCircle },
  { id: 'key_clauses', label: 'Key Clauses', icon: Hash },
  { id: 'risk_flags', label: 'Risk Flags', icon: ShieldAlert },
];

const severityStyles: Record<string, string> = { low: 'badge-gray', medium: 'badge-yellow', high: 'badge-red', critical: 'badge-red' };
const urgencyStyles: Record<string, string> = { low: 'badge-gray', medium: 'badge-blue', high: 'badge-yellow', critical: 'badge-red' };

export default function DocumentDetailPage() {
  const { id: matterId, docId } = useParams<{ id: string; docId: string }>();
  const { data: doc, isLoading } = useDocument(docId);
  const reprocess = useReprocessDocument(docId);
  const [activeExtraction, setActiveExtraction] = useState('summary');

  if (isLoading || !doc) {
    return <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-32 bg-slate-100 rounded-xl animate-pulse" />)}</div>;
  }

  const getExtraction = (type: string) => doc.extractions.find(e => e.extraction_type === type);
  const activeData = getExtraction(activeExtraction);

  return (
    <div>
      <Link href={`/matters/${matterId}`} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-4">
        <ArrowLeft className="h-4 w-4" /> Back to Matter
      </Link>

      {/* doc info header */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-red-500 text-sm font-bold uppercase">{doc.file_type}</div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">{doc.filename}</h1>
              <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                {doc.file_size_bytes && <span>{(doc.file_size_bytes / 1024 / 1024).toFixed(1)} MB</span>}
                {doc.page_count && <span>· {doc.page_count} pages</span>}
                <span>· Uploaded {format(new Date(doc.created_at), 'MMM d, yyyy')}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {doc.processing_status === 'completed' && (
              <span className="badge-green flex items-center gap-1.5"><Sparkles className="h-3 w-3" /> AI Analyzed</span>
            )}
            {doc.processing_status === 'processing' && (
              <span className="badge-blue flex items-center gap-1.5"><RefreshCw className="h-3 w-3 animate-spin" /> Processing...</span>
            )}
            {doc.processing_status === 'failed' && (
              <span className="badge-red flex items-center gap-1.5"><AlertTriangle className="h-3 w-3" /> Failed</span>
            )}
            <button onClick={() => reprocess.mutate()} className="btn-secondary text-xs" disabled={reprocess.isPending}>
              <RefreshCw className={`h-3.5 w-3.5 ${reprocess.isPending ? 'animate-spin' : ''}`} /> Reprocess
            </button>
          </div>
        </div>

        {/* confidence score bar */}
        {activeData?.confidence_score && (
          <div className="mt-4 flex items-center gap-2">
            <div className="h-1.5 flex-1 max-w-xs rounded-full bg-slate-100">
              <div className="h-1.5 rounded-full bg-emerald-500 transition-all" style={{ width: `${(activeData.confidence_score * 100)}%` }} />
            </div>
            <span className="text-xs font-medium text-slate-500">{Math.round(activeData.confidence_score * 100)}% confidence</span>
          </div>
        )}
      </div>

      {/* extraction type tabs */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {extractionTabs.map(tab => {
          const ext = getExtraction(tab.id);
          const hasData = ext && (tab.id === 'summary' ? ext.extracted_data?.text : ext.extracted_data?.items?.length > 0);
          return (
            <button
              key={tab.id}
              onClick={() => setActiveExtraction(tab.id)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-all ${
                activeExtraction === tab.id
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : hasData
                    ? 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50'
                    : 'bg-slate-50 text-slate-400 ring-1 ring-slate-100'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
              {hasData && tab.id !== 'summary' && (
                <span className={`ml-1 text-xs font-bold ${activeExtraction === tab.id ? 'text-indigo-200' : 'text-slate-400'}`}>
                  {ext?.extracted_data?.items?.length || 0}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* extracted content */}
      <div className="animate-fade-in">
        {!activeData ? (
          <div className="card p-12 text-center">
            <FileText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500">No {activeExtraction} data extracted</p>
          </div>
        ) : activeExtraction === 'summary' ? (
          <div className="card p-6">
            <p className="text-sm text-slate-700 leading-relaxed">{activeData.extracted_data?.text || 'No summary available.'}</p>
          </div>
        ) : activeExtraction === 'parties' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(activeData.extracted_data?.items || []).map((party: any, i: number) => (
              <div key={i} className="card p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-sm font-bold text-indigo-700">
                    {party.name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900">{party.name}</p>
                    <span className="badge-indigo capitalize">{party.role}</span>
                  </div>
                </div>
                {party.context && <p className="text-xs text-slate-500 mt-2">{party.context}</p>}
              </div>
            ))}
          </div>
        ) : activeExtraction === 'deadlines' ? (
          <div className="space-y-3">
            {(activeData.extracted_data?.items || []).map((d: any, i: number) => (
              <div key={i} className="card p-5 flex items-start gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600 shrink-0">
                  <Clock className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-slate-900">{d.description}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    {d.date && <span className="text-xs font-medium text-slate-700">{format(new Date(d.date), 'MMMM d, yyyy')}</span>}
                    <span className={urgencyStyles[d.urgency] || 'badge-gray'}>{d.urgency}</span>
                  </div>
                  {d.source_text && <p className="text-xs text-slate-400 mt-2 italic">&ldquo;{d.source_text}&rdquo;</p>}
                </div>
              </div>
            ))}
          </div>
        ) : activeExtraction === 'obligations' ? (
          <div className="space-y-3">
            {(activeData.extracted_data?.items || []).map((o: any, i: number) => (
              <div key={i} className="card p-5">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="badge-blue">{o.party}</span>
                  {o.clause_reference && <span className="text-xs text-slate-400">{o.clause_reference}</span>}
                </div>
                <p className="text-sm text-slate-700">{o.obligation}</p>
                {o.due_date && <p className="text-xs text-slate-500 mt-1.5">Due: {format(new Date(o.due_date), 'MMMM d, yyyy')}</p>}
              </div>
            ))}
          </div>
        ) : activeExtraction === 'key_clauses' ? (
          <div className="space-y-3">
            {(activeData.extracted_data?.items || []).map((c: any, i: number) => (
              <div key={i} className="card p-5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="badge-purple capitalize">{c.clause_type?.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-sm text-slate-700">{c.summary}</p>
                {c.source_text && <p className="text-xs text-slate-400 mt-2 italic border-l-2 border-slate-200 pl-3">{c.source_text}</p>}
              </div>
            ))}
          </div>
        ) : activeExtraction === 'risk_flags' ? (
          <div className="space-y-3">
            {(activeData.extracted_data?.items || []).map((r: any, i: number) => (
              <div key={i} className="card p-5 border-l-4 border-l-red-400">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-bold text-slate-900 capitalize">{r.flag_type?.replace(/_/g, ' ')}</span>
                  <span className={severityStyles[r.severity]}>{r.severity}</span>
                </div>
                <p className="text-sm text-slate-600">{r.description}</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
