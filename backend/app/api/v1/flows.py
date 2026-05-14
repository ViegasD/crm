from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.flow import Flow, FlowExecution
from app.models.workspace import User
from app.schemas.flow import FlowCreate, FlowExecutionOut, FlowOut, FlowUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/flows", tags=["flows"])


@router.post("", response_model=FlowOut, status_code=201)
async def create_flow(
    workspace_id: UUID,
    body: FlowCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    flow = Flow(
        workspace_id=workspace_id,
        name=body.name,
        trigger_type=body.trigger_type,
        channel_account_id=body.channel_account_id,
        nodes_data=body.graph.model_dump() if body.graph else {},
        active=False,
    )
    db.add(flow)
    await db.flush()
    return flow


@router.get("", response_model=list[FlowOut])
async def list_flows(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Flow).where(Flow.workspace_id == workspace_id))
    return result.scalars().all()


@router.get("/{flow_id}", response_model=FlowOut)
async def get_flow(
    workspace_id: UUID,
    flow_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    flow = await db.get(Flow, flow_id)
    if not flow or flow.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


@router.patch("/{flow_id}", response_model=FlowOut)
async def update_flow(
    workspace_id: UUID,
    flow_id: UUID,
    body: FlowUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    flow = await db.get(Flow, flow_id)
    if not flow or flow.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Flow not found")
    data = body.model_dump(exclude_none=True)
    if "graph" in data:
        flow.nodes_data = data.pop("graph")
    for field, val in data.items():
        setattr(flow, field, val)
    return flow


@router.delete("/{flow_id}", status_code=204)
async def delete_flow(
    workspace_id: UUID,
    flow_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    flow = await db.get(Flow, flow_id)
    if not flow or flow.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Flow not found")
    await db.delete(flow)


@router.post("/{flow_id}/activate", response_model=FlowOut)
async def activate_flow(
    workspace_id: UUID,
    flow_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    flow = await db.get(Flow, flow_id)
    if not flow or flow.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Flow not found")
    flow.active = True
    return flow


@router.post("/{flow_id}/deactivate", response_model=FlowOut)
async def deactivate_flow(
    workspace_id: UUID,
    flow_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    flow = await db.get(Flow, flow_id)
    if not flow or flow.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Flow not found")
    flow.active = False
    return flow
