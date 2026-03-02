import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type {
  Matter, MatterDetail, MatterListResponse, Document, DocumentDetail,
  Task, TimelineEvent, SearchResponse, DashboardStats, Notification,
  AuditLog, MemberWithUser, Organization,
} from '@/types';

function useOrgId() {
  const { orgId } = useAuth();
  return orgId;
}

// dashboard stats
export function useDashboard() {
  const orgId = useOrgId();
  return useQuery<DashboardStats>({
    queryKey: ['dashboard', orgId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/dashboard`)).data,
    enabled: !!orgId,
  });
}

// get all matters with optional filters
export function useMatters(params?: { status?: string; search?: string; page?: number }) {
  const orgId = useOrgId();
  return useQuery<MatterListResponse>({
    queryKey: ['matters', orgId, params],
    queryFn: async () => (await api.get(`/orgs/${orgId}/matters`, { params })).data,
    enabled: !!orgId,
  });
}

export function useMatter(matterId: string) {
  const orgId = useOrgId();
  return useQuery<MatterDetail>({
    queryKey: ['matter', matterId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/matters/${matterId}`)).data,
    enabled: !!orgId && !!matterId,
  });
}

export function useCreateMatter() {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => (await api.post(`/orgs/${orgId}/matters`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['matters'] }),
  });
}

export function useUpdateMatter(matterId: string) {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => (await api.patch(`/orgs/${orgId}/matters/${matterId}`, data)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['matter', matterId] });
      qc.invalidateQueries({ queryKey: ['matters'] });
    },
  });
}

// document hooks
export function useDocuments(matterId: string) {
  const orgId = useOrgId();
  return useQuery<Document[]>({
    queryKey: ['documents', matterId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/matters/${matterId}/documents`)).data,
    enabled: !!orgId && !!matterId,
  });
}

export function useDocument(docId: string) {
  const orgId = useOrgId();
  return useQuery<DocumentDetail>({
    queryKey: ['document', docId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/documents/${docId}`)).data,
    enabled: !!orgId && !!docId,
  });
}

export function useUploadDocument(matterId: string) {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return (await api.post(`/orgs/${orgId}/matters/${matterId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })).data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', matterId] });
      qc.invalidateQueries({ queryKey: ['matter', matterId] });
    },
  });
}

export function useReprocessDocument(docId: string) {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post(`/orgs/${orgId}/documents/${docId}/reprocess`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['document', docId] }),
  });
}

// task hooks
export function useTasks(params?: { status?: string; assigned_to_me?: boolean }) {
  const orgId = useOrgId();
  return useQuery<{ items: Task[]; total: number }>({
    queryKey: ['tasks', orgId, params],
    queryFn: async () => (await api.get(`/orgs/${orgId}/tasks`, { params })).data,
    enabled: !!orgId,
  });
}

export function useMatterTasks(matterId: string) {
  const orgId = useOrgId();
  return useQuery<{ items: Task[]; total: number }>({
    queryKey: ['tasks', matterId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/matters/${matterId}/tasks`)).data,
    enabled: !!orgId && !!matterId,
  });
}

export function useCreateTask(matterId: string) {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => (await api.post(`/orgs/${orgId}/matters/${matterId}/tasks`, data)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] });
      qc.invalidateQueries({ queryKey: ['matter', matterId] });
    },
  });
}

export function useUpdateTask() {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ taskId, data }: { taskId: string; data: any }) =>
      (await api.patch(`/orgs/${orgId}/tasks/${taskId}`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }),
  });
}

// timeline stuff
export function useTimeline(matterId: string) {
  const orgId = useOrgId();
  return useQuery<TimelineEvent[]>({
    queryKey: ['timeline', matterId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/matters/${matterId}/timeline`)).data,
    enabled: !!orgId && !!matterId,
  });
}

export function useCreateTimelineEvent(matterId: string) {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => (await api.post(`/orgs/${orgId}/matters/${matterId}/timeline`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['timeline', matterId] }),
  });
}

// semantic search
export function useSearch() {
  const orgId = useOrgId();
  return useMutation<SearchResponse, Error, { query: string; matter_id?: string }>({
    mutationFn: async (data) => (await api.post(`/orgs/${orgId}/search`, data)).data,
  });
}

// notifications
export function useNotifications() {
  const orgId = useOrgId();
  return useQuery<{ items: Notification[]; unread_count: number }>({
    queryKey: ['notifications', orgId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/notifications`)).data,
    enabled: !!orgId,
    refetchInterval: 30000,
  });
}

export function useMarkNotificationRead() {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (notifId: string) => (await api.patch(`/orgs/${orgId}/notifications/${notifId}/read`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useMarkAllRead() {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post(`/orgs/${orgId}/notifications/read-all`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

// org and members
export function useOrganization() {
  const orgId = useOrgId();
  return useQuery<Organization>({
    queryKey: ['organization', orgId],
    queryFn: async () => (await api.get(`/orgs/${orgId}`)).data,
    enabled: !!orgId,
  });
}

export function useMembers() {
  const orgId = useOrgId();
  return useQuery<MemberWithUser[]>({
    queryKey: ['members', orgId],
    queryFn: async () => (await api.get(`/orgs/${orgId}/members`)).data,
    enabled: !!orgId,
  });
}

export function useInviteMember() {
  const orgId = useOrgId();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: any) => (await api.post(`/orgs/${orgId}/members/invite`, data)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members'] }),
  });
}

// audit log
export function useAuditLogs(params?: { page?: number; resource_type?: string }) {
  const orgId = useOrgId();
  return useQuery<{ items: AuditLog[]; total: number }>({
    queryKey: ['audit-logs', orgId, params],
    queryFn: async () => (await api.get(`/orgs/${orgId}/audit-logs`, { params })).data,
    enabled: !!orgId,
  });
}
