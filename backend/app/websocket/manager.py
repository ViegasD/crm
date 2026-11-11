import json
from collections import defaultdict
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from fastapi import WebSocket
from jose import JWTError
from sqlalchemy import select

from app.core.conversation_access import conversation_access_clause
from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.conversation import Conversation
from app.models.workspace import UserWorkspaceMembership


@dataclass(frozen=True)
class ConnectionIdentity:
    user_id: UUID
    token: str


class ConnectionManager:
    """Per-workspace WebSocket room manager."""

    def __init__(self):
        # workspace_id -> set of WebSocket connections
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._identities: dict[WebSocket, ConnectionIdentity] = {}
        self._pending: ContextVar[list | None] = ContextVar("websocket_pending", default=None)

    @asynccontextmanager
    async def committed_events(self, db):
        """Publish this task's events only after its database changes commit.

        Captures nested service broadcasts too (e.g. first-message assignment).
        A rollback discards the batch. This is not a durable/cross-process outbox.
        """
        pending = []
        token = self._pending.set(pending)
        try:
            yield
            await db.commit()
        except BaseException:
            await db.rollback()
            raise
        finally:
            self._pending.reset(token)
        for workspace_id, payload, target in pending:
            await self.broadcast(workspace_id, payload, target_user_id=target)

    async def connect(self, workspace_id: str, websocket: WebSocket, user_id: UUID, token: str) -> None:
        await websocket.accept()
        self._rooms[workspace_id].add(websocket)
        self._identities[websocket] = ConnectionIdentity(user_id, token)

    def disconnect(self, workspace_id: str, websocket: WebSocket) -> None:
        room = self._rooms.get(workspace_id)
        if room is not None:
            room.discard(websocket)
            if not room:
                del self._rooms[workspace_id]
        self._identities.pop(websocket, None)

    async def authorized(self, workspace_id: str, websocket: WebSocket, db) -> bool:
        identity = self._identities.get(websocket)
        if identity is None:
            return False
        try:
            payload = decode_token(identity.token)
            if payload.get("type") != "access" or UUID(str(payload.get("sub"))) != identity.user_id:
                return False
            workspace = UUID(workspace_id)
        except (JWTError, ValueError, TypeError):
            return False
        return await db.scalar(select(UserWorkspaceMembership.id).where(
            UserWorkspaceMembership.workspace_id == workspace,
            UserWorkspaceMembership.user_id == identity.user_id,
        )) is not None

    async def revoke(self, workspace_id: str, websocket: WebSocket) -> None:
        self.disconnect(workspace_id, websocket)
        await websocket.close(code=4003)

    async def broadcast(self, workspace_id: str, payload: dict, *, target_user_id: str | None = None) -> None:
        """Check current membership and visibility before each delivery.

        This is process-local transport; cross-process fanout is AUD06. Database
        or malformed-event errors fail closed instead of falling back to a room.
        """
        pending = self._pending.get()
        if pending is not None:
            pending.append((workspace_id, dict(payload), target_user_id))
            return
        sockets = list(self._rooms.get(workspace_id, []))
        if not sockets:
            return
        try:
            workspace = UUID(workspace_id)
            raw_conversation = payload.get("conversation_id")
            conversation_id = UUID(str(raw_conversation)) if raw_conversation is not None else None
            # A user_id in presence/assignment events is the event's subject,
            # not its recipient. Only notifications or send_to target a user.
            raw_target = target_user_id or (payload.get("user_id") if payload.get("type") == "notification" else None)
            target = UUID(str(raw_target)) if raw_target else None
        except (ValueError, TypeError):
            return
        async with AsyncSessionLocal() as db:
            for ws in sockets:
                try:
                    if not await self.authorized(workspace_id, ws, db):
                        await self.revoke(workspace_id, ws)
                        continue
                    identity = self._identities[ws]
                    if target is not None and identity.user_id != target:
                        continue
                    if conversation_id is not None:
                        visible = await db.scalar(select(Conversation.id).where(
                            Conversation.id == conversation_id,
                            conversation_access_clause(workspace, identity.user_id),
                        ))
                        if visible is None:
                            continue
                    await ws.send_text(json.dumps(payload))
                except Exception:
                    # Never send private data when an authorization lookup fails.
                    await db.rollback()
                    self.disconnect(workspace_id, ws)
                    try:
                        await ws.close(code=1011)
                    except Exception:
                        pass

    async def send_to(self, workspace_id: str, user_id: str, payload: dict) -> None:
        await self.broadcast(workspace_id, payload, target_user_id=user_id)


manager = ConnectionManager()
