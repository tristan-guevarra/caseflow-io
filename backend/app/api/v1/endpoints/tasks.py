# task management endpoints

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import RequireRole, require_lawyer
from app.models.matter import Matter
from app.models.task import Task
from app.models.user import Membership, User
from app.schemas.documents import CreateTaskRequest, TaskListResponse, TaskResponse, UpdateTaskRequest
from app.services.audit import create_audit_log

router = APIRouter(tags=["Tasks"])


@router.get("/orgs/{org_id}/tasks", response_model=TaskListResponse)
async def list_org_tasks(
    org_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    assigned_to_me: bool = Query(False),
):
    # list all tasks for the org, with optional filters
    query = select(Task).where(Task.organization_id == org_id)

    if status_filter:
        query = query.where(Task.status == status_filter)
    if priority:
        query = query.where(Task.priority == priority)
    if assigned_to_me:
        query = query.where(Task.assigned_to_id == membership.user_id)

    query = query.order_by(Task.due_date.asc().nullslast(), Task.priority.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()

    # add matter titles and assignee names to each task
    items = []
    for task in tasks:
        matter = (await db.execute(select(Matter.title).where(Matter.id == task.matter_id))).scalar_one_or_none()
        assignee_name = None
        if task.assigned_to_id:
            assignee_name = (await db.execute(
                select(User.full_name).where(User.id == task.assigned_to_id)
            )).scalar_one_or_none()
        items.append(TaskResponse(
            **{k: v for k, v in TaskResponse.model_validate(task).model_dump().items()
               if k not in ("matter_title", "assigned_to_name")},
            matter_title=matter,
            assigned_to_name=assignee_name,
        ))

    return TaskListResponse(items=items, total=len(items))


@router.get("/orgs/{org_id}/matters/{matter_id}/tasks", response_model=TaskListResponse)
async def list_matter_tasks(
    org_id: UUID,
    matter_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # get tasks for a specific matter
    result = await db.execute(
        select(Task)
        .where(Task.organization_id == org_id, Task.matter_id == matter_id)
        .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
    )
    tasks = result.scalars().all()
    items = [TaskResponse.model_validate(t) for t in tasks]
    return TaskListResponse(items=items, total=len(items))


@router.post("/orgs/{org_id}/matters/{matter_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    org_id: UUID,
    matter_id: UUID,
    payload: CreateTaskRequest,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # create a new task manually
    task = Task(
        organization_id=org_id,
        matter_id=matter_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
        assigned_to_id=payload.assigned_to_id,
        created_by="manual",
    )
    db.add(task)
    await db.flush()

    await create_audit_log(
        db,
        organization_id=org_id,
        user_id=membership.user_id,
        action="task.created",
        resource_type="task",
        resource_id=task.id,
        details={"title": task.title, "matter_id": str(matter_id)},
    )

    return TaskResponse.model_validate(task)


@router.patch("/orgs/{org_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    org_id: UUID,
    task_id: UUID,
    payload: UpdateTaskRequest,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # update a task
    task = (await db.execute(
        select(Task).where(Task.id == task_id, Task.organization_id == org_id)
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True)

    # if marking as complete, set the completed_at timestamp
    if update_data.get("status") == "completed" and task.status != "completed":
        task.completed_at = datetime.now(timezone.utc)
    elif update_data.get("status") and update_data["status"] != "completed":
        task.completed_at = None

    for field, value in update_data.items():
        setattr(task, field, value)

    return TaskResponse.model_validate(task)
