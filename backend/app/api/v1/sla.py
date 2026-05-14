from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.sla import AgentCapacity, SlaPolicy
from app.models.workspace import User
from app.schemas.sla import AgentCapacityOut, AgentCapacitySet, SlaPolicyCreate, SlaPolicyOut, SlaPolicyUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/sla", tags=["sla"])


@router.post("/policies", response_model=SlaPolicyOut, status_code=201)
async def create_policy(
    workspace_id: UUID,
    body: SlaPolicyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = SlaPolicy(
        workspace_id=workspace_id,
        name=body.name,
        sector_id=body.sector_id,
        first_response_minutes=body.first_response_minutes,
        resolution_minutes=body.resolution_minutes,
        active=body.active,
    )
    db.add(policy)
    await db.flush()
    return policy


@router.get("/policies", response_model=list[SlaPolicyOut])
async def list_policies(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(SlaPolicy).where(SlaPolicy.workspace_id == workspace_id))
    return result.scalars().all()


@router.patch("/policies/{policy_id}", response_model=SlaPolicyOut)
async def update_policy(
    workspace_id: UUID,
    policy_id: UUID,
    body: SlaPolicyUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = await db.get(SlaPolicy, policy_id)
    if not policy or policy.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(policy, field, val)
    return policy


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    workspace_id: UUID,
    policy_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    policy = await db.get(SlaPolicy, policy_id)
    if not policy or policy.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Policy not found")
    await db.delete(policy)


# Agent capacity
@router.put("/capacity", response_model=AgentCapacityOut)
async def set_capacity(
    workspace_id: UUID,
    body: AgentCapacitySet,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentCapacity).where(
            AgentCapacity.workspace_id == workspace_id,
            AgentCapacity.user_id == body.user_id,
        )
    )
    cap = result.scalar_one_or_none()
    if cap:
        cap.max_conversations = body.max_conversations
        cap.sector_id = body.sector_id
    else:
        cap = AgentCapacity(
            workspace_id=workspace_id,
            user_id=body.user_id,
            max_conversations=body.max_conversations,
            sector_id=body.sector_id,
        )
        db.add(cap)
    await db.flush()
    return cap


@router.get("/capacity", response_model=list[AgentCapacityOut])
async def list_capacity(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(AgentCapacity).where(AgentCapacity.workspace_id == workspace_id)
    )
    return result.scalars().all()
