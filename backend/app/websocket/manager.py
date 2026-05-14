import json
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    """Per-workspace WebSocket room manager."""

    def __init__(self):
        # workspace_id -> set of WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, workspace_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms[workspace_id].add(websocket)

    def disconnect(self, workspace_id: str, websocket: WebSocket) -> None:
        self._rooms[workspace_id].discard(websocket)
        if not self._rooms[workspace_id]:
            del self._rooms[workspace_id]

    async def broadcast(self, workspace_id: str, payload: dict) -> None:
        """Send a JSON payload to all connections in a workspace room."""
        dead: list[WebSocket] = []
        for ws in list(self._rooms.get(workspace_id, [])):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(workspace_id, ws)

    async def send_to(self, workspace_id: str, user_id: str, payload: dict) -> None:
        """Placeholder for targeted sends (requires per-user tracking if needed)."""
        await self.broadcast(workspace_id, payload)


manager = ConnectionManager()
