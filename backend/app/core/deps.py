# fastapi dependencies for auth, role checks, and tenant scoping

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, has_minimum_role
from app.models.user import Membership, User

bearer_scheme = HTTPBearer()


# pull user from jwt token - used as a dependency everywhere
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == UUID(user_id), User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or deactivated")
    return user


# check that the user actually belongs to this org
async def get_current_membership(
    org_id: Annotated[UUID, Path(alias="org_id")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Membership:
    result = await db.execute(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.organization_id == org_id,
            Membership.is_active == True,  # noqa: E712
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
    # stash user on membership so we can grab it later
    membership._user = current_user  # type: ignore[attr-defined]
    return membership


# dependency class that checks if user has high enough role
class RequireRole:

    def __init__(self, minimum_role: str):
        self.minimum_role = minimum_role

    async def __call__(
        self,
        membership: Annotated[Membership, Depends(get_current_membership)],
    ) -> Membership:
        if not has_minimum_role(membership.role, self.minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least '{self.minimum_role}' role",
            )
        return membership


# shorthand role dependencies
require_admin = RequireRole("admin")
require_lawyer = RequireRole("lawyer")
require_paralegal = RequireRole("paralegal")
