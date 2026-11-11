from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from asyncio import TimeoutError, wait_for
from jose import JWTError
from uuid import UUID
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.workspace import UserWorkspaceMembership
from app.services.presence_idle import mark_agent_active
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    # Authenticate via token query param: ws://host/ws/{workspace_id}?token=<jwt>
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError
        user_id = UUID(str(payload.get("sub")))
        workspace_uuid = UUID(workspace_id)
    except (JWTError, ValueError, TypeError):
        await websocket.close(code=4001)
        return

    # Canonicalize the room ID, so alternate UUID spellings cannot create rooms
    # whose broadcasts bypass or miss the normal workspace key.
    workspace_id = str(workspace_uuid)
    async with AsyncSessionLocal() as db:
        member = await db.scalar(select(UserWorkspaceMembership.id).where(
            UserWorkspaceMembership.workspace_id == workspace_uuid,
            UserWorkspaceMembership.user_id == user_id,
        ))
    if member is None:
        await websocket.close(code=4003)
        return
    await manager.connect(workspace_id, websocket, user_id, token)
    try:
        await mark_agent_active(workspace_uuid, user_id)
        while True:
            # Recheck idle sessions as well as every incoming frame. Broadcasts
            # independently recheck before sending, so revoked users get no data.
            try:
                data = await wait_for(websocket.receive_text(), timeout=15)
            except TimeoutError:
                data = None
            async with AsyncSessionLocal() as db:
                allowed = await manager.authorized(workspace_id, websocket, db)
            if not allowed:
                await manager.revoke(workspace_id, websocket)
                return
            if data == "ping":
                await mark_agent_active(workspace_uuid, user_id)
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(workspace_id, websocket)
