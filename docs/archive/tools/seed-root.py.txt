"""
Seed a dev user + workspace.
Run from the backend/ directory:

    python seed.py

Credentials created:
    email:    admin@crm.dev
    password: admin123
"""
import asyncio
import os

# Manually parse env files so DATABASE_URL is set before imports
def _load_env(path: str, override: bool = False) -> None:
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip()
            if override or k not in os.environ:
                os.environ[k] = v

ROOT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

_load_env(os.path.join(BACKEND_DIR, ".env"))
_load_env(os.path.join(BACKEND_DIR, ".env.local"), override=True)
_load_env(os.path.join(ROOT_DIR, ".env"), override=True)
_load_env(os.path.join(ROOT_DIR, ".env.local"), override=True)

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.workspace import User, Workspace, UserWorkspaceMembership
from app.models.enums import WorkspaceRole, UserStatus
from app.core.security import hash_password


async def seed() -> None:
    async with AsyncSessionLocal() as db:  # type: AsyncSession
        from sqlalchemy import select

        # Idempotent: skip if user already exists
        existing = await db.scalar(select(User).where(User.email == "admin@crm.dev"))
        if existing:
            print("User admin@crm.dev already exists — nothing to do.")
            return

        user = User(
            name="Admin",
            email="admin@crm.dev",
            password_hash=hash_password("admin123"),
            status=UserStatus.offline,
        )
        db.add(user)
        await db.flush()

        workspace = Workspace(name="Default Workspace", slug="default", plan="free")
        db.add(workspace)
        await db.flush()

        membership = UserWorkspaceMembership(
            user_id=user.id,
            workspace_id=workspace.id,
            role=WorkspaceRole.admin,
        )
        db.add(membership)
        await db.commit()

        print(f"Created user {user.email} (id={user.id})")
        print(f"Created workspace '{workspace.name}' (id={workspace.id})")
        print("Login with: admin@crm.dev / admin123")


if __name__ == "__main__":
    asyncio.run(seed())
