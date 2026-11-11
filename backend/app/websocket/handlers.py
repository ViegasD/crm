from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from uuid import UUID

from app.core.security import decode_token
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
    except (JWTError, ValueError):
        await websocket.close(code=4001)
        return

    await manager.connect(workspace_id, websocket)
    await mark_agent_active(workspace_uuid, user_id)
    try:
        while True:
            # Keep connection alive; client may send pings
            data = await websocket.receive_text()
            if data == "ping":
                await mark_agent_active(workspace_uuid, user_id)
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(workspace_id, websocket)
