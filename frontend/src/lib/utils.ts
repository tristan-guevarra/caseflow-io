import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { formatDistanceToNow, format, isToday, isTomorrow, isPast, differenceInDays } from 'date-fns';

// merge tailwind classes without conflicts
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// format a date string to like "Jan 5, 2026"
export function formatDate(date: string | null | undefined): string {
  if (!date) return '—';
  return format(new Date(date), 'MMM d, yyyy');
}

// format with time included
export function formatDateTime(date: string | null | undefined): string {
  if (!date) return '—';
  return format(new Date(date), 'MMM d, yyyy h:mm a');
}

// shows "2 hours ago" style text
export function formatRelative(date: string | null | undefined): string {
  if (!date) return '—';
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

// turn bytes into human readable file size
export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// figure out how urgent a deadline is and pick a color
export function getDeadlineUrgency(dateStr: string | null): { label: string; color: string } {
  if (!dateStr) return { label: 'No date', color: 'text-slate-400' };
  const d = new Date(dateStr);
  const days = differenceInDays(d, new Date());
  if (isPast(d)) return { label: 'Overdue', color: 'text-red-600' };
  if (isToday(d)) return { label: 'Due today', color: 'text-red-600' };
  if (isTomorrow(d)) return { label: 'Due tomorrow', color: 'text-orange-500' };
  if (days <= 7) return { label: `${days} days`, color: 'text-amber-600' };
  if (days <= 30) return { label: `${days} days`, color: 'text-slate-600' };
  return { label: `${days} days`, color: 'text-slate-400' };
}

// matter type display names
export const MATTER_TYPE_LABELS: Record<string, string> = {
  litigation: 'Litigation',
  corporate: 'Corporate',
  real_estate: 'Real Estate',
  ip: 'Intellectual Property',
  employment: 'Employment',
  family: 'Family',
  criminal: 'Criminal',
  other: 'Other',
};

// badge colors for each matter type
export const MATTER_TYPE_COLORS: Record<string, string> = {
  litigation: 'bg-red-50 text-red-700 ring-red-600/20',
  corporate: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  real_estate: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  ip: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  employment: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  family: 'bg-pink-50 text-pink-700 ring-pink-600/20',
  criminal: 'bg-slate-50 text-slate-700 ring-slate-600/20',
  other: 'bg-gray-50 text-gray-700 ring-gray-600/20',
};

// colors for matter status badges
export const STATUS_COLORS: Record<string, string> = {
  active: 'bg-green-50 text-green-700 ring-green-600/20',
  pending: 'bg-yellow-50 text-yellow-700 ring-yellow-600/20',
  closed: 'bg-slate-50 text-slate-700 ring-slate-600/20',
  archived: 'bg-gray-50 text-gray-500 ring-gray-500/20',
};

// priority level styling
export const PRIORITY_CONFIG: Record<string, { color: string; bg: string; dot: string }> = {
  urgent: { color: 'text-red-700', bg: 'bg-red-50', dot: 'bg-red-500' },
  high: { color: 'text-orange-700', bg: 'bg-orange-50', dot: 'bg-orange-500' },
  medium: { color: 'text-blue-700', bg: 'bg-blue-50', dot: 'bg-blue-500' },
  low: { color: 'text-slate-600', bg: 'bg-slate-50', dot: 'bg-slate-400' },
};

// processing status labels and colors
export const PROCESSING_STATUS_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  pending: { label: 'Pending', color: 'text-slate-500', icon: '⏳' },
  processing: { label: 'Processing', color: 'text-blue-600', icon: '⚙️' },
  completed: { label: 'Completed', color: 'text-green-600', icon: '✓' },
  failed: { label: 'Failed', color: 'text-red-600', icon: '✗' },
};

// timeline dot colors by category
export const TIMELINE_CATEGORY_COLORS: Record<string, string> = {
  filing: 'bg-blue-500',
  hearing: 'bg-purple-500',
  deadline: 'bg-red-500',
  correspondence: 'bg-green-500',
  meeting: 'bg-amber-500',
  custom: 'bg-slate-400',
};
