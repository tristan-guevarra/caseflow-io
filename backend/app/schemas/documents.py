# schemas for documents, extractions, tasks, timeline, search, audit, notifications, dashboard

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# document response
class DocumentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    matter_id: UUID
    uploaded_by_id: UUID | None = None
    filename: str
    file_type: str
    file_size_bytes: int | None = None
    processing_status: str
    processing_error: str | None = None
    page_count: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    extractions: list["ExtractionResponse"] = []


# what the ai extraction looks like
class ExtractionResponse(BaseModel):
    id: UUID
    document_id: UUID
    extraction_type: str
    extracted_data: dict
    confidence_score: float | None = None
    model_version: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# schema for validating the full ai extraction output
class AIExtractionResult(BaseModel):
    summary: str
    parties: list[dict] = []
    deadlines: list[dict] = []
    obligations: list[dict] = []
    key_clauses: list[dict] = []
    risk_flags: list[dict] = []
    key_dates: list[dict] = []


# task create/update/response
class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    due_date: date | None = None
    assigned_to_id: UUID | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: str | None = Field(None, pattern="^(pending|in_progress|completed|canceled)$")
    priority: str | None = Field(None, pattern="^(low|medium|high|urgent)$")
    due_date: date | None = None
    assigned_to_id: UUID | None = None


class TaskResponse(BaseModel):
    id: UUID
    organization_id: UUID
    matter_id: UUID
    document_id: UUID | None = None
    title: str
    description: str | None = None
    status: str
    priority: str
    due_date: date | None = None
    assigned_to_id: UUID | None = None
    created_by: str
    source_extraction_id: UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    matter_title: str | None = None
    assigned_to_name: str | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


# timeline event schemas
class CreateTimelineEventRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    event_date: date
    category: str = Field(default="custom", pattern="^(filing|hearing|deadline|correspondence|meeting|custom)$")


class UpdateTimelineEventRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    event_date: date | None = None
    category: str | None = Field(None, pattern="^(filing|hearing|deadline|correspondence|meeting|custom)$")


class TimelineEventResponse(BaseModel):
    id: UUID
    matter_id: UUID
    document_id: UUID | None = None
    title: str
    description: str | None = None
    event_date: date
    category: str
    source: str
    created_by_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# semantic search schemas
class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    matter_id: UUID | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    document_id: UUID
    document_filename: str
    matter_id: UUID
    matter_title: str
    chunk_text: str
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int


# audit log schemas
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: UUID | None = None
    details: dict
    ip_address: str | None = None
    created_at: datetime
    user_name: str | None = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int


# notification schemas
class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str | None = None
    notification_type: str
    is_read: bool
    link: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int


# dashboard stats
class DashboardStats(BaseModel):
    active_matters: int
    open_tasks: int
    upcoming_deadlines: int
    documents_processed: int
    recent_activity: list[AuditLogResponse] = []
    upcoming_tasks: list[TaskResponse] = []
