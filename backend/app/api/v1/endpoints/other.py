# timeline, search, org management, dashboard, notifications, and audit log endpoints

from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RequireRole, get_current_user, require_admin, require_lawyer
from app.models.document import Document, Embedding
from app.models.matter import Matter
from app.models.task import AuditLog, Notification, Task, TimelineEvent
from app.models.user import Membership, Organization, User
from app.schemas.auth import (
    InviteMemberRequest,
    MemberWithUser,
    MembershipResponse,
    OrganizationResponse,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
    UserResponse,
)
from app.schemas.documents import (
    AuditLogListResponse,
    AuditLogResponse,
    CreateTimelineEventRequest,
    DashboardStats,
    NotificationListResponse,
    NotificationResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    TaskResponse,
    TimelineEventResponse,
    UpdateTimelineEventRequest,
)
from app.core.security import hash_password
from app.services.ai import generate_single_embedding
from app.services.audit import create_audit_log

# timeline

timeline_router = APIRouter(tags=["Timeline"])


@timeline_router.get("/orgs/{org_id}/matters/{matter_id}/timeline", response_model=list[TimelineEventResponse])
async def list_timeline_events(
    org_id: UUID,
    matter_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = Query(None),
):
    # get timeline events for a matter, oldest first
    query = select(TimelineEvent).where(
        TimelineEvent.organization_id == org_id,
        TimelineEvent.matter_id == matter_id,
    )
    if category:
        query = query.where(TimelineEvent.category == category)

    query = query.order_by(TimelineEvent.event_date.asc())
    result = await db.execute(query)
    return [TimelineEventResponse.model_validate(e) for e in result.scalars().all()]


@timeline_router.post(
    "/orgs/{org_id}/matters/{matter_id}/timeline",
    response_model=TimelineEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_timeline_event(
    org_id: UUID,
    matter_id: UUID,
    payload: CreateTimelineEventRequest,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # add a manual timeline event
    event = TimelineEvent(
        organization_id=org_id,
        matter_id=matter_id,
        title=payload.title,
        description=payload.description,
        event_date=payload.event_date,
        category=payload.category,
        source="manual",
        created_by_id=membership.user_id,
    )
    db.add(event)
    await db.flush()
    return TimelineEventResponse.model_validate(event)


@timeline_router.patch("/orgs/{org_id}/timeline/{event_id}", response_model=TimelineEventResponse)
async def update_timeline_event(
    org_id: UUID,
    event_id: UUID,
    payload: UpdateTimelineEventRequest,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # update a timeline event
    event = (await db.execute(
        select(TimelineEvent).where(TimelineEvent.id == event_id, TimelineEvent.organization_id == org_id)
    )).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Timeline event not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    return TimelineEventResponse.model_validate(event)


@timeline_router.delete("/orgs/{org_id}/timeline/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeline_event(
    org_id: UUID,
    event_id: UUID,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # delete a timeline event
    event = (await db.execute(
        select(TimelineEvent).where(TimelineEvent.id == event_id, TimelineEvent.organization_id == org_id)
    )).scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Timeline event not found")
    await db.delete(event)


# semantic search

search_router = APIRouter(tags=["Search"])


@search_router.post("/orgs/{org_id}/search", response_model=SearchResponse)
async def semantic_search(
    org_id: UUID,
    payload: SearchRequest,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # turn the query into an embedding and search against stored doc chunks
    query_embedding = generate_single_embedding(payload.query)
    if not query_embedding:
        return SearchResponse(query=payload.query, results=[], total=0)

    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # pgvector cosine similarity search
    sql = text("""
        SELECT
            e.document_id,
            e.chunk_text,
            1 - (e.embedding <=> :embedding::vector) AS similarity,
            d.filename,
            d.matter_id,
            m.title AS matter_title
        FROM embeddings e
        JOIN documents d ON d.id = e.document_id
        JOIN matters m ON m.id = d.matter_id
        WHERE e.organization_id = :org_id
        ORDER BY e.embedding <=> :embedding::vector
        LIMIT :limit
    """)

    params = {"org_id": str(org_id), "embedding": embedding_str, "limit": payload.limit}

    # if they want to search within a specific matter only
    if payload.matter_id:
        sql = text("""
            SELECT
                e.document_id,
                e.chunk_text,
                1 - (e.embedding <=> :embedding::vector) AS similarity,
                d.filename,
                d.matter_id,
                m.title AS matter_title
            FROM embeddings e
            JOIN documents d ON d.id = e.document_id
            JOIN matters m ON m.id = d.matter_id
            WHERE e.organization_id = :org_id AND d.matter_id = :matter_id
            ORDER BY e.embedding <=> :embedding::vector
            LIMIT :limit
        """)
        params["matter_id"] = str(payload.matter_id)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    results = [
        SearchResultItem(
            document_id=row.document_id,
            document_filename=row.filename,
            matter_id=row.matter_id,
            matter_title=row.matter_title,
            chunk_text=row.chunk_text[:500],
            similarity_score=round(float(row.similarity), 4),
        )
        for row in rows
    ]

    return SearchResponse(query=payload.query, results=results, total=len(results))


# organizations

org_router = APIRouter(tags=["Organizations"])


@org_router.get("/orgs/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationResponse.model_validate(org)


@org_router.patch("/orgs/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    payload: UpdateOrganizationRequest,
    membership: Annotated[Membership, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, field, value)

    return OrganizationResponse.model_validate(org)


@org_router.get("/orgs/{org_id}/members", response_model=list[MemberWithUser])
async def list_members(
    org_id: UUID,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # get all active members with their user info
    result = await db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.organization_id == org_id, Membership.is_active == True)  # noqa: E712
    )
    rows = result.all()
    return [
        MemberWithUser(
            **MembershipResponse.model_validate(m).model_dump(),
            user=UserResponse.model_validate(u),
        )
        for m, u in rows
    ]


@org_router.post("/orgs/{org_id}/members/invite", response_model=MemberWithUser, status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: UUID,
    payload: InviteMemberRequest,
    membership: Annotated[Membership, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # invite a user to the org - creates their account if they don't exist yet
    existing_user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()

    if existing_user:
        # check if they're already a member
        existing_membership = (await db.execute(
            select(Membership).where(
                Membership.user_id == existing_user.id,
                Membership.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if existing_membership:
            raise HTTPException(status_code=409, detail="User is already a member")
        user = existing_user
    else:
        # create new user with a temp password (should trigger password reset email)
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password("TempPass123!"),
        )
        db.add(user)
        await db.flush()

    new_membership = Membership(user_id=user.id, organization_id=org_id, role=payload.role)
    db.add(new_membership)
    await db.flush()

    await create_audit_log(
        db,
        organization_id=org_id,
        user_id=membership.user_id,
        action="member.invited",
        resource_type="membership",
        resource_id=new_membership.id,
        details={"email": payload.email, "role": payload.role},
    )

    return MemberWithUser(
        **MembershipResponse.model_validate(new_membership).model_dump(),
        user=UserResponse.model_validate(user),
    )


@org_router.patch("/orgs/{org_id}/members/{member_id}", response_model=MembershipResponse)
async def update_member_role(
    org_id: UUID,
    member_id: UUID,
    payload: UpdateMemberRoleRequest,
    membership: Annotated[Membership, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    target = (await db.execute(
        select(Membership).where(Membership.id == member_id, Membership.organization_id == org_id)
    )).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found")

    target.role = payload.role

    await create_audit_log(
        db,
        organization_id=org_id,
        user_id=membership.user_id,
        action="member.role_changed",
        resource_type="membership",
        resource_id=target.id,
        details={"new_role": payload.role},
    )

    return MembershipResponse.model_validate(target)


@org_router.delete("/orgs/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    member_id: UUID,
    membership: Annotated[Membership, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    target = (await db.execute(
        select(Membership).where(Membership.id == member_id, Membership.organization_id == org_id)
    )).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Membership not found")

    if target.user_id == membership.user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    # soft delete - just deactivate
    target.is_active = False


# dashboard

dashboard_router = APIRouter(tags=["Dashboard"])


@dashboard_router.get("/orgs/{org_id}/dashboard", response_model=DashboardStats)
async def get_dashboard(
    org_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # count up all the stats for the dashboard
    active_matters = (await db.execute(
        select(func.count()).where(Matter.organization_id == org_id, Matter.status == "active")
    )).scalar() or 0

    open_tasks = (await db.execute(
        select(func.count()).where(
            Task.organization_id == org_id,
            Task.status.in_(["pending", "in_progress"]),
        )
    )).scalar() or 0

    upcoming_deadlines = (await db.execute(
        select(func.count()).where(
            Task.organization_id == org_id,
            Task.due_date != None,  # noqa: E711
            Task.due_date <= date.today() + timedelta(days=7),
            Task.status.in_(["pending", "in_progress"]),
        )
    )).scalar() or 0

    docs_processed = (await db.execute(
        select(func.count()).where(
            Document.organization_id == org_id,
            Document.processing_status == "completed",
        )
    )).scalar() or 0

    # grab recent audit log entries
    activity_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
    )
    recent_activity = [AuditLogResponse.model_validate(a) for a in activity_result.scalars().all()]

    # grab tasks coming up soon
    tasks_result = await db.execute(
        select(Task)
        .where(
            Task.organization_id == org_id,
            Task.status.in_(["pending", "in_progress"]),
            Task.due_date != None,  # noqa: E711
        )
        .order_by(Task.due_date.asc())
        .limit(10)
    )
    upcoming_tasks = [TaskResponse.model_validate(t) for t in tasks_result.scalars().all()]

    return DashboardStats(
        active_matters=active_matters,
        open_tasks=open_tasks,
        upcoming_deadlines=upcoming_deadlines,
        documents_processed=docs_processed,
        recent_activity=recent_activity,
        upcoming_tasks=upcoming_tasks,
    )


# notifications

notification_router = APIRouter(tags=["Notifications"])


@notification_router.get("/orgs/{org_id}/notifications", response_model=NotificationListResponse)
async def list_notifications(
    org_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # get the user's notifications, newest first
    result = await db.execute(
        select(Notification)
        .where(Notification.organization_id == org_id, Notification.user_id == membership.user_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    notifications = [NotificationResponse.model_validate(n) for n in result.scalars().all()]

    unread_count = (await db.execute(
        select(func.count()).where(
            Notification.organization_id == org_id,
            Notification.user_id == membership.user_id,
            Notification.is_read == False,  # noqa: E712
        )
    )).scalar() or 0

    return NotificationListResponse(items=notifications, unread_count=unread_count)


@notification_router.patch("/orgs/{org_id}/notifications/{notif_id}/read")
async def mark_notification_read(
    org_id: UUID,
    notif_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # mark a single notification as read
    notif = (await db.execute(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.organization_id == org_id,
            Notification.user_id == membership.user_id,
        )
    )).scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    return {"status": "ok"}


@notification_router.post("/orgs/{org_id}/notifications/read-all")
async def mark_all_read(
    org_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # mark all notifications as read for this user
    await db.execute(
        Notification.__table__.update()
        .where(
            Notification.organization_id == org_id,
            Notification.user_id == membership.user_id,
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    return {"status": "ok"}


# audit logs

audit_router = APIRouter(tags=["Audit Logs"])


@audit_router.get("/orgs/{org_id}/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    org_id: UUID,
    membership: Annotated[Membership, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    resource_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    # list audit logs with optional resource type filter
    query = select(AuditLog).where(AuditLog.organization_id == org_id)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [AuditLogResponse.model_validate(a) for a in result.scalars().all()]

    return AuditLogListResponse(items=items, total=total)
