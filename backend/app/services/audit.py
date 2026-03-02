# writes audit log entries to the db for tracking who did what

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import AuditLog


# save an audit log entry
async def create_audit_log(
    db: AsyncSession,
    *,
    organization_id: UUID,
    user_id: UUID | None = None,
    action: str,
    resource_type: str,
    resource_id: UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    log = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(log)
    await db.flush()
    return log
