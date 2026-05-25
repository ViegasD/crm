from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    auth,
    canned_responses,
    catalog,
    channel_accounts,
    contacts,
    conversation_policies,
    conversations,
    flows,
    labels,
    macros,
    media,
    messages,
    sectors,
    sla,
    users,
    public,
    stage9_extras,
    webhook_events,
    webhook_ops,
    workspaces,
)
from app.core.redis import close_redis, get_redis
from app.webhooks.whatsapp import evolution as evolution_webhook
from app.webhooks.whatsapp import meta as meta_webhook
from app.websocket.handlers import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await get_redis()
    yield
    # shutdown
    await close_redis()


app = FastAPI(title="CRM API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth / User
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

# ── Workspaces & sub-resources
app.include_router(workspaces.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(channel_accounts.router, prefix="/api/v1")
app.include_router(contacts.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(conversation_policies.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(labels.router, prefix="/api/v1")
app.include_router(canned_responses.router, prefix="/api/v1")
app.include_router(macros.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(webhook_events.router, prefix="/api/v1")
app.include_router(webhook_ops.router, prefix="/api/v1")
app.include_router(stage9_extras.router, prefix="/api/v1")
app.include_router(public.router, prefix="/api/v1")
app.include_router(flows.router, prefix="/api/v1")
app.include_router(sla.router, prefix="/api/v1")

# ── Media
app.include_router(media.router, prefix="/api/v1")

# ── Webhooks
app.include_router(meta_webhook.router)
app.include_router(evolution_webhook.router)

# ── WebSocket
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
