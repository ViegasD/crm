"""Run inside the backend container with bootstrap JSON on stdin.

The caller generates/stores the password privately; it is never printed here.
"""
import asyncio
import json
import sys

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import WorkspaceRole
from app.models.workspace import User, UserWorkspaceMembership, Workspace


async def bootstrap(values):
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == values["email"]))
        if user is None:
            user = User(name="CRM2 Development Admin", email=values["email"],
                        password_hash=hash_password(values["password"]))
            db.add(user)
            await db.flush()
        workspace = await db.scalar(select(Workspace).where(Workspace.slug == "crm2-development"))
        if workspace is None:
            workspace = Workspace(name="CRM2 Development", slug="crm2-development")
            db.add(workspace)
            await db.flush()
        membership = await db.scalar(select(UserWorkspaceMembership).where(
            UserWorkspaceMembership.user_id == user.id,
            UserWorkspaceMembership.workspace_id == workspace.id))
        if membership is None:
            db.add(UserWorkspaceMembership(user_id=user.id, workspace_id=workspace.id,
                                           role=WorkspaceRole.admin))
        await db.commit()
        print(json.dumps({"adminCreated": True, "workspaceId": str(workspace.id)}))


if __name__ == "__main__":
    asyncio.run(bootstrap(json.load(sys.stdin)))
