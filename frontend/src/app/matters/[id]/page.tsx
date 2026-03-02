'use client';

import { useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useMatter, useDocuments, useMatterTasks, useTimeline, useUploadDocument, useUpdateTask } from '@/hooks/useApi';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowLeft, Upload, FileText, CheckSquare, Clock, Sparkles, AlertTriangle, Users, MapPin, Calendar, MoreVertical, RefreshCw } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { format, formatDistanceToNow, isPast, differenceInDays } from 'date-fns';
import toast from 'react-hot-toast';

const statusStyles: Record<string, string> = { active: 'badge-green', pending: 'badge-yellow', closed: 'badge-gray', archived: 'badge-gray' };
const priorityStyles: Record<string, string> = { urgent: 'badge-red', high: 'badge-yellow', medium: 'badge-blue', low: 'badge-gray' };
const processingStyles: Record<string, string> = { pending: 'badge-yellow', processing: 'badge-blue', completed: 'badge-green', failed: 'badge-red' };
const categoryIcons: Record<string, string> = { filing: '📋', hearing: '⚖️', deadline: '⏰', correspondence: '📨', meeting: '🤝', custom: '📌' };

const tabs = [
  { id: 'overview', label: 'Overview', icon: Sparkles },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare },
  { id: 'timeline', label: 'Timeline', icon: Clock },
];

export default function MatterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { currentMembership } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  const { data: matter, isLoading } = useMatter(id);
  const { data: documents } = useDocuments(id);
  const { data: tasksData } = useMatterTasks(id);
  const { data: timeline } = useTimeline(id);
  const uploadDoc = useUploadDocument(id);
  const updateTask = useUpdateTask();

  // handle file drops for document upload
  const onDrop = useCallback(async (files: File[]) => {
    for (const file of files) {
      try {
        await uploadDoc.mutateAsync(file);
        toast.success(`"${file.name}" uploaded — AI processing started`);
      } catch {
        toast.error(`Failed to upload ${file.name}`);
      }
    }
  }, [uploadDoc]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxSize: 25 * 1024 * 1024,
  });

  if (isLoading || !matter) {
    return <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 bg-slate-100 rounded-xl animate-pulse" />)}</div>;
  }

  const isLawyer = currentMembership?.role !== 'paralegal';

  return (
    <div>
      {/* back link and header */}
      <Link href="/matters" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-4">
        <ArrowLeft className="h-4 w-4" /> All Matters
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-bold text-slate-900">{matter.title}</h1>
            <span className={statusStyles[matter.status]}>{matter.status}</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            {matter.case_number && <span>{matter.case_number}</span>}
            {matter.client_name && <span>· {matter.client_name}</span>}
            {matter.jurisdiction && <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{matter.jurisdiction}</span>}
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-1.5 text-slate-500">
            <FileText className="h-4 w-4" /> {matter.document_count} docs
          </div>
          <div className="flex items-center gap-1.5 text-slate-500">
            <CheckSquare className="h-4 w-4" /> {matter.open_task_count}/{matter.task_count} tasks
          </div>
        </div>
      </div>

      {/* tab navigation */}
      <div className="flex gap-1 border-b border-slate-200 mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
            {tab.id === 'tasks' && matter.open_task_count > 0 && (
              <span className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-100 text-[10px] font-bold text-indigo-600">{matter.open_task_count}</span>
            )}
          </button>
        ))}
      </div>

      {/* overview tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">
          <div className="lg:col-span-2 space-y-6">
            {matter.description && (
              <div className="card p-6">
                <h3 className="text-sm font-semibold text-slate-900 mb-2">Description</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{matter.description}</p>
              </div>
            )}
            {matter.opposing_party && (
              <div className="card p-6">
                <h3 className="text-sm font-semibold text-slate-900 mb-2">Opposing Party</h3>
                <p className="text-sm text-slate-600">{matter.opposing_party}</p>
              </div>
            )}
          </div>
          <div className="space-y-6">
            {/* team members */}
            <div className="card p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2"><Users className="h-4 w-4 text-slate-400" /> Team</h3>
              <div className="space-y-2.5">
                {matter.assignments.map(a => (
                  <div key={a.id} className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-700">
                      {a.user_name?.split(' ').map(n => n[0]).join('') || '?'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{a.user_name}</p>
                      <p className="text-xs text-slate-400 capitalize">{a.role}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* key dates */}
            <div className="card p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2"><Calendar className="h-4 w-4 text-slate-400" /> Key Dates</h3>
              <div className="text-sm text-slate-600 space-y-1.5">
                <p>Opened: {format(new Date(matter.opened_at), 'MMM d, yyyy')}</p>
                {matter.closed_at && <p>Closed: {format(new Date(matter.closed_at), 'MMM d, yyyy')}</p>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* documents tab */}
      {activeTab === 'documents' && (
        <div className="animate-fade-in space-y-4">
          {/* drag and drop upload zone */}
          <div
            {...getRootProps()}
            className={`card border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
              isDragActive ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 hover:border-indigo-300 hover:bg-slate-50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className={`h-8 w-8 mx-auto mb-3 ${isDragActive ? 'text-indigo-500' : 'text-slate-400'}`} />
            <p className="text-sm font-medium text-slate-700">{isDragActive ? 'Drop files here...' : 'Drag & drop documents, or click to browse'}</p>
            <p className="text-xs text-slate-400 mt-1">PDF or DOCX · Max 25MB · AI extraction will run automatically</p>
          </div>

          {/* document list table */}
          {documents && documents.length > 0 ? (
            <div className="table-container">
              <table className="w-full">
                <thead><tr className="table-header">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Document</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Size</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Uploaded</th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {documents.map(doc => (
                    <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-3.5">
                        <Link href={`/matters/${id}/documents/${doc.id}`} className="flex items-center gap-3 group">
                          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-50 text-red-500 text-xs font-bold uppercase">{doc.file_type}</div>
                          <span className="text-sm font-medium text-slate-900 group-hover:text-indigo-600 transition-colors">{doc.filename}</span>
                        </Link>
                      </td>
                      <td className="px-6 py-3.5">
                        <span className={`${processingStyles[doc.processing_status]} flex items-center gap-1.5`}>
                          {doc.processing_status === 'processing' && <RefreshCw className="h-3 w-3 animate-spin" />}
                          {doc.processing_status === 'completed' && <Sparkles className="h-3 w-3" />}
                          {doc.processing_status}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-sm text-slate-500">
                        {doc.file_size_bytes ? `${(doc.file_size_bytes / 1024 / 1024).toFixed(1)} MB` : '—'}
                      </td>
                      <td className="px-6 py-3.5 text-xs text-slate-400">{formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="card p-12 text-center">
              <FileText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-500">No documents yet</p>
              <p className="text-xs text-slate-400 mt-1">Upload your first document to start AI extraction.</p>
            </div>
          )}
        </div>
      )}

      {/* tasks tab */}
      {activeTab === 'tasks' && (
        <div className="animate-fade-in space-y-3">
          {tasksData?.items.length === 0 ? (
            <div className="card p-12 text-center">
              <CheckSquare className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-500">No tasks yet</p>
              <p className="text-xs text-slate-400 mt-1">Upload documents to auto-generate tasks from deadlines.</p>
            </div>
          ) : (
            tasksData?.items.map(task => {
              const daysLeft = task.due_date ? differenceInDays(new Date(task.due_date), new Date()) : null;
              const overdue = task.due_date ? isPast(new Date(task.due_date)) : false;
              return (
                <div key={task.id} className="card p-4 flex items-center gap-4 hover:shadow-sm transition-shadow">
                  {/* toggle complete checkbox */}
                  <button
                    onClick={() => {
                      const newStatus = task.status === 'completed' ? 'pending' : 'completed';
                      updateTask.mutate({ taskId: task.id, data: { status: newStatus } });
                    }}
                    className={`flex h-5 w-5 items-center justify-center rounded border-2 transition-colors ${
                      task.status === 'completed' ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-300 hover:border-indigo-400'
                    }`}
                  >
                    {task.status === 'completed' && <span className="text-xs">✓</span>}
                  </button>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${task.status === 'completed' ? 'line-through text-slate-400' : 'text-slate-900'}`}>
                      {task.title}
                    </p>
                    {task.description && <p className="text-xs text-slate-400 mt-0.5 truncate">{task.description}</p>}
                  </div>
                  {task.created_by === 'ai' && <span className="badge-indigo flex items-center gap-1"><Sparkles className="h-3 w-3" /> AI</span>}
                  <span className={priorityStyles[task.priority]}>{task.priority}</span>
                  {task.due_date && (
                    <span className={`text-xs font-medium ${overdue ? 'text-red-600' : daysLeft !== null && daysLeft <= 3 ? 'text-amber-600' : 'text-slate-500'}`}>
                      {format(new Date(task.due_date), 'MMM d')}
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* timeline tab */}
      {activeTab === 'timeline' && (
        <div className="animate-fade-in">
          {timeline && timeline.length > 0 ? (
            <div className="relative pl-8 space-y-0">
              <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-slate-200" />
              {timeline.map((event, i) => (
                <div key={event.id} className="relative pb-6">
                  <div className={`absolute left-[-20px] top-1 flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                    event.source === 'ai_extracted' ? 'bg-indigo-100' : 'bg-white border-2 border-slate-300'
                  }`}>
                    {categoryIcons[event.category] || '📌'}
                  </div>
                  <div className="card p-4 ml-4">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-semibold text-slate-900">{event.title}</p>
                      {event.source === 'ai_extracted' && <span className="badge-indigo text-[10px] flex items-center gap-0.5"><Sparkles className="h-2.5 w-2.5" />AI</span>}
                    </div>
                    <p className="text-xs text-slate-500">{format(new Date(event.event_date), 'MMMM d, yyyy')}</p>
                    {event.description && <p className="text-xs text-slate-400 mt-1">{event.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card p-12 text-center">
              <Clock className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-500">No timeline events yet</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
