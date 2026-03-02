// auth types
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface Membership {
  id: string;
  user_id: string;
  organization_id: string;
  role: 'admin' | 'lawyer' | 'paralegal';
  is_active: boolean;
  joined_at: string;
}

export interface UserWithMemberships extends User {
  memberships: Membership[];
}

// org stuff
export interface Organization {
  id: string;
  name: string;
  slug: string;
  subscription_tier: string;
  subscription_status: string;
  max_users: number;
  max_storage_mb: number;
  created_at: string;
}

export interface MemberWithUser extends Membership {
  user: User;
}

// matter types
export type MatterType = 'litigation' | 'corporate' | 'real_estate' | 'ip' | 'employment' | 'family' | 'criminal' | 'other';
export type MatterStatus = 'active' | 'pending' | 'closed' | 'archived';

export interface Matter {
  id: string;
  organization_id: string;
  title: string;
  case_number: string | null;
  client_name: string | null;
  matter_type: MatterType;
  status: MatterStatus;
  jurisdiction: string | null;
  opposing_party: string | null;
  description: string | null;
  opened_at: string;
  closed_at: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MatterDetail extends Matter {
  assignments: Assignment[];
  document_count: number;
  task_count: number;
  open_task_count: number;
}

export interface Assignment {
  id: string;
  matter_id: string;
  user_id: string;
  role: 'lead' | 'contributor' | 'viewer';
  assigned_at: string;
  user_name: string | null;
  user_email: string | null;
}

export interface MatterListResponse {
  items: Matter[];
  total: number;
  page: number;
  page_size: number;
}

// document types
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Document {
  id: string;
  organization_id: string;
  matter_id: string;
  uploaded_by_id: string | null;
  filename: string;
  file_type: string;
  file_size_bytes: number | null;
  processing_status: ProcessingStatus;
  processing_error: string | null;
  page_count: number | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document {
  extractions: Extraction[];
}

export interface Extraction {
  id: string;
  document_id: string;
  extraction_type: 'parties' | 'deadlines' | 'obligations' | 'key_clauses' | 'risk_flags' | 'summary';
  extracted_data: Record<string, any>;
  confidence_score: number | null;
  model_version: string | null;
  created_at: string;
}

// task types
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'canceled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string;
  organization_id: string;
  matter_id: string;
  document_id: string | null;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  assigned_to_id: string | null;
  created_by: 'ai' | 'manual';
  source_extraction_id: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  matter_title?: string | null;
  assigned_to_name?: string | null;
}

// timeline events
export interface TimelineEvent {
  id: string;
  matter_id: string;
  document_id: string | null;
  title: string;
  description: string | null;
  event_date: string;
  category: 'filing' | 'hearing' | 'deadline' | 'correspondence' | 'meeting' | 'custom';
  source: 'ai_extracted' | 'manual' | 'system';
  created_by_id: string | null;
  created_at: string;
}

// search types
export interface SearchResult {
  document_id: string;
  document_filename: string;
  matter_id: string;
  matter_title: string;
  chunk_text: string;
  similarity_score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

// dashboard stats
export interface DashboardStats {
  active_matters: number;
  open_tasks: number;
  upcoming_deadlines: number;
  documents_processed: number;
  recent_activity: AuditLog[];
  upcoming_tasks: Task[];
}

// notification types
export interface Notification {
  id: string;
  title: string;
  message: string | null;
  notification_type: string;
  is_read: boolean;
  link: string | null;
  created_at: string;
}

// audit log
export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any>;
  ip_address: string | null;
  created_at: string;
  user_name?: string | null;
}
