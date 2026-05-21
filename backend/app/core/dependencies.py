from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Returns the authenticated User ORM object. Raises 401 on failure."""
    from app.models.workspace import User  # local import to avoid circular

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, UUID(user_id))
    if user is None:
        raise credentials_exception
    return user


async def get_workspace_member(
    workspace_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns (user, membership) for workspace_id. Raises 403 if not a member."""
    from app.models.workspace import UserWorkspaceMembership

    result = await db.execute(
        select(UserWorkspaceMembership).where(
            UserWorkspaceMembership.user_id == current_user.id,
            UserWorkspaceMembership.workspace_id == workspace_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return current_user, membership


async def require_workspace_member(
    workspace_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Same as get_workspace_member but returns the User directly.

    Use this as a dependency on workspace-scoped routes to enforce membership
    without changing existing handler signatures.
    """
    from app.models.workspace import UserWorkspaceMembership

    result = await db.execute(
        select(UserWorkspaceMembership).where(
            UserWorkspaceMembership.user_id == current_user.id,
            UserWorkspaceMembership.workspace_id == workspace_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return current_user


def require_roles(*roles: str):
    """Dependency factory that checks the membership role.

    Returns a callable that resolves to the User for compatibility with handlers
    that previously expected `current_user`.
    """

    async def _check(
        workspace_id: UUID,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        from app.models.workspace import UserWorkspaceMembership

        result = await db.execute(
            select(UserWorkspaceMembership).where(
                UserWorkspaceMembership.user_id == current_user.id,
                UserWorkspaceMembership.workspace_id == workspace_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        if membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(roles)}",
            )
        return current_user

    return _check
