# matter management endpoints - crud + assignments

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import RequireRole, get_current_user, require_lawyer
from app.models.matter import Matter, MatterAssignment
from app.models.document import Document
from app.models.task import Task
from app.models.user import Membership, User
from app.schemas.matter import (
    AssignMatterRequest,
    AssignmentResponse,
    CreateMatterRequest,
    MatterDetailResponse,
    MatterListResponse,
    MatterResponse,
    UpdateMatterRequest,
)
from app.services.audit import create_audit_log

router = APIRouter(prefix="/orgs/{org_id}/matters", tags=["Matters"])


@router.get("", response_model=MatterListResponse)
async def list_matters(
    org_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
    matter_type: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    # grab all matters for this org with optional filters
    query = select(Matter).where(Matter.organization_id == org_id)

    if status_filter:
        query = query.where(Matter.status == status_filter)
    if matter_type:
        query = query.where(Matter.matter_type == matter_type)
    if search:
        query = query.where(
            Matter.title.ilike(f"%{search}%")
            | Matter.client_name.ilike(f"%{search}%")
            | Matter.case_number.ilike(f"%{search}%")
        )

    # paralegals can only see matters they're assigned to
    if membership.role == "paralegal":
        query = query.join(MatterAssignment).where(MatterAssignment.user_id == membership.user_id)

    # get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # paginate results
    query = query.order_by(Matter.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    matters = result.scalars().all()

    return MatterListResponse(
        items=[MatterResponse.model_validate(m) for m in matters],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
async def create_matter(
    org_id: UUID,
    payload: CreateMatterRequest,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # create a new matter
    matter = Matter(
        organization_id=org_id,
        title=payload.title,
        case_number=payload.case_number,
        client_name=payload.client_name,
        matter_type=payload.matter_type,
        jurisdiction=payload.jurisdiction,
        opposing_party=payload.opposing_party,
        description=payload.description,
        created_by_id=membership.user_id,
    )
    db.add(matter)
    await db.flush()

    # auto-assign the creator as lead
    assignment = MatterAssignment(
        matter_id=matter.id,
        user_id=membership.user_id,
        role="lead",
    )
    db.add(assignment)

    await create_audit_log(
        db,
        organization_id=org_id,
        user_id=membership.user_id,
        action="matter.created",
        resource_type="matter",
        resource_id=matter.id,
        details={"title": matter.title},
    )

    return MatterResponse.model_validate(matter)


@router.get("/{matter_id}", response_model=MatterDetailResponse)
async def get_matter(
    org_id: UUID,
    matter_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # get matter with assignments and user info
    result = await db.execute(
        select(Matter)
        .where(Matter.id == matter_id, Matter.organization_id == org_id)
        .options(selectinload(Matter.assignments).selectinload(MatterAssignment.user))
    )
    matter = result.scalar_one_or_none()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # count docs and tasks for this matter
    doc_count = (await db.execute(
        select(func.count()).where(Document.matter_id == matter_id)
    )).scalar() or 0

    task_count = (await db.execute(
        select(func.count()).where(Task.matter_id == matter_id)
    )).scalar() or 0

    open_task_count = (await db.execute(
        select(func.count()).where(Task.matter_id == matter_id, Task.status.in_(["pending", "in_progress"]))
    )).scalar() or 0

    assignments = [
        AssignmentResponse(
            id=a.id,
            matter_id=a.matter_id,
            user_id=a.user_id,
            role=a.role,
            assigned_at=a.assigned_at,
            user_name=a.user.full_name if a.user else None,
            user_email=a.user.email if a.user else None,
        )
        for a in matter.assignments
    ]

    return MatterDetailResponse(
        **MatterResponse.model_validate(matter).model_dump(),
        assignments=assignments,
        document_count=doc_count,
        task_count=task_count,
        open_task_count=open_task_count,
    )


@router.patch("/{matter_id}", response_model=MatterResponse)
async def update_matter(
    org_id: UUID,
    matter_id: UUID,
    payload: UpdateMatterRequest,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # update a matter's fields
    result = await db.execute(
        select(Matter).where(Matter.id == matter_id, Matter.organization_id == org_id)
    )
    matter = result.scalar_one_or_none()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(matter, field, value)

    await create_audit_log(
        db,
        organization_id=org_id,
        user_id=membership.user_id,
        action="matter.updated",
        resource_type="matter",
        resource_id=matter.id,
        details={"fields_updated": list(update_data.keys())},
    )

    return MatterResponse.model_validate(matter)


@router.post("/{matter_id}/assign", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_matter(
    org_id: UUID,
    matter_id: UUID,
    payload: AssignMatterRequest,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # make sure the matter exists
    matter = (await db.execute(
        select(Matter).where(Matter.id == matter_id, Matter.organization_id == org_id)
    )).scalar_one_or_none()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # make sure the user is in this org
    target_membership = (await db.execute(
        select(Membership).where(
            Membership.user_id == payload.user_id,
            Membership.organization_id == org_id,
            Membership.is_active == True,  # noqa: E712
        )
    )).scalar_one_or_none()
    if not target_membership:
        raise HTTPException(status_code=400, detail="User is not a member of this organization")

    # don't assign someone twice
    existing = (await db.execute(
        select(MatterAssignment).where(
            MatterAssignment.matter_id == matter_id,
            MatterAssignment.user_id == payload.user_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="User already assigned to this matter")

    assignment = MatterAssignment(
        matter_id=matter_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    db.add(assignment)
    await db.flush()

    # get user info to include in the response
    user = (await db.execute(select(User).where(User.id == payload.user_id))).scalar_one()

    return AssignmentResponse(
        id=assignment.id,
        matter_id=assignment.matter_id,
        user_id=assignment.user_id,
        role=assignment.role,
        assigned_at=assignment.assigned_at,
        user_name=user.full_name,
        user_email=user.email,
    )
