# schemas for matters and matter assignments

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateMatterRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    case_number: str | None = Field(None, max_length=100)
    client_name: str | None = Field(None, max_length=255)
    matter_type: str = Field(pattern="^(litigation|corporate|real_estate|ip|employment|family|criminal|other)$")
    jurisdiction: str | None = Field(None, max_length=255)
    opposing_party: str | None = Field(None, max_length=255)
    description: str | None = None


class UpdateMatterRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    case_number: str | None = Field(None, max_length=100)
    client_name: str | None = Field(None, max_length=255)
    status: str | None = Field(None, pattern="^(active|pending|closed|archived)$")
    jurisdiction: str | None = Field(None, max_length=255)
    opposing_party: str | None = Field(None, max_length=255)
    description: str | None = None


class MatterResponse(BaseModel):
    id: UUID
    organization_id: UUID
    title: str
    case_number: str | None = None
    client_name: str | None = None
    matter_type: str
    status: str
    jurisdiction: str | None = None
    opposing_party: str | None = None
    description: str | None = None
    opened_at: date
    closed_at: date | None = None
    created_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatterDetailResponse(MatterResponse):
    assignments: list["AssignmentResponse"] = []
    document_count: int = 0
    task_count: int = 0
    open_task_count: int = 0


class MatterListResponse(BaseModel):
    items: list[MatterResponse]
    total: int
    page: int
    page_size: int


class AssignMatterRequest(BaseModel):
    user_id: UUID
    role: str = Field(default="contributor", pattern="^(lead|contributor|viewer)$")


class AssignmentResponse(BaseModel):
    id: UUID
    matter_id: UUID
    user_id: UUID
    role: str
    assigned_at: datetime
    user_name: str | None = None
    user_email: str | None = None

    model_config = {"from_attributes": True}
