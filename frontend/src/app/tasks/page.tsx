'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTasks, useUpdateTask } from '@/hooks/useApi';
import { CheckSquare, Sparkles, Filter } from 'lucide-react';
import { format, isPast, differenceInDays } from 'date-fns';

const priorityStyles: Record<string, string> = { urgent: 'badge-red', high: 'badge-yellow', medium: 'badge-blue', low: 'badge-gray' };
const statusLabels: Record<string, string> = { pending: 'To Do', in_progress: 'In Progress', completed: 'Done', canceled: 'Canceled' };

export default function TasksPage() {
  const [filter, setFilter] = useState<string>('');
  const [myTasks, setMyTasks] = useState(false);
  const { data, isLoading } = useTasks({ status: filter || undefined, assigned_to_me: myTasks || undefined });
  const updateTask = useUpdateTask();

  // group tasks by status for display
  const groupedTasks = {
    overdue: (data?.items || []).filter(t => t.due_date && isPast(new Date(t.due_date)) && t.status !== 'completed' && t.status !== 'canceled'),
    upcoming: (data?.items || []).filter(t => !t.due_date || (!isPast(new Date(t.due_date)) && t.status !== 'completed' && t.status !== 'canceled')),
    completed: (data?.items || []).filter(t => t.status === 'completed' || t.status === 'canceled'),
  };

  const TaskRow = ({ task }: { task: any }) => {
    const daysLeft = task.due_date ? differenceInDays(new Date(task.due_date), new Date()) : null;
    return (
      <div className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50 transition-colors border-b border-slate-100 last:border-0">
        <button
          onClick={() => updateTask.mutate({ taskId: task.id, data: { status: task.status === 'completed' ? 'pending' : 'completed' } })}
          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors ${
            task.status === 'completed' ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-slate-300 hover:border-indigo-400'
          }`}
        >
          {task.status === 'completed' && <span className="text-[10px]">✓</span>}
        </button>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium ${task.status === 'completed' ? 'line-through text-slate-400' : 'text-slate-900'}`}>{task.title}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {task.matter_title && (
              <Link href={`/matters/${task.matter_id}`} className="text-xs text-slate-400 hover:text-indigo-500 transition-colors">{task.matter_title}</Link>
            )}
          </div>
        </div>
        {task.created_by === 'ai' && <span className="badge-indigo text-[10px] flex items-center gap-0.5"><Sparkles className="h-2.5 w-2.5" />AI</span>}
        <span className={priorityStyles[task.priority]}>{task.priority}</span>
        {task.assigned_to_name && <span className="text-xs text-slate-400 hidden md:block">{task.assigned_to_name}</span>}
        {task.due_date && (
          <span className={`text-xs font-medium whitespace-nowrap ${
            isPast(new Date(task.due_date)) && task.status !== 'completed' ? 'text-red-600' : daysLeft !== null && daysLeft <= 3 ? 'text-amber-600' : 'text-slate-500'
          }`}>
            {format(new Date(task.due_date), 'MMM d')}
          </span>
        )}
      </div>
    );
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Tasks</h1>
        <p className="page-description">All tasks across your matters, including AI-generated deadlines.</p>
      </div>

      {/* filter controls */}
      <div className="flex items-center gap-3 mb-6">
        <select className="input w-44" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="pending">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>
        <button onClick={() => setMyTasks(!myTasks)} className={`btn-secondary text-xs ${myTasks ? 'ring-2 ring-indigo-200 bg-indigo-50 text-indigo-700' : ''}`}>
          My Tasks Only
        </button>
        <span className="text-sm text-slate-400 ml-auto">{data?.total || 0} tasks</span>
      </div>

      {isLoading ? (
        <div className="card">{[1,2,3,4].map(i => <div key={i} className="h-14 border-b border-slate-100 animate-pulse bg-slate-50" />)}</div>
      ) : (
        <div className="space-y-6">
          {groupedTasks.overdue.length > 0 && (
            <div>
              <h2 className="text-xs font-bold text-red-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">⚠️ Overdue ({groupedTasks.overdue.length})</h2>
              <div className="card">{groupedTasks.overdue.map(t => <TaskRow key={t.id} task={t} />)}</div>
            </div>
          )}
          {groupedTasks.upcoming.length > 0 && (
            <div>
              <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Active ({groupedTasks.upcoming.length})</h2>
              <div className="card">{groupedTasks.upcoming.map(t => <TaskRow key={t.id} task={t} />)}</div>
            </div>
          )}
          {groupedTasks.completed.length > 0 && (
            <div>
              <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Completed ({groupedTasks.completed.length})</h2>
              <div className="card opacity-60">{groupedTasks.completed.map(t => <TaskRow key={t.id} task={t} />)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
