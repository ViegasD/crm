"""Admin endpoints for Stage 4 Tier 2: rotation, IP allowlist, circuit,
attempts diff, latency stats."""
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.channel import ChannelAccount, ChannelCredential
from app.models.webhook_ops import (
    ChannelCircuitState,
    WebhookEventAttempt,
    WebhookIpAllowlist,
)
from app.models.workspace import User
from app.schemas.webhook_ops import (
    ChannelCircuitOut,
    CredentialRotateRequest,
    CredentialRotationOut,
    LatencyStats,
    WebhookAttemptOut,
    WebhookIpAllowlistCreate,
    WebhookIpAllowlistOut,
)
from app.services.webhook_ops_service import (
    finalize_rotation,
    manual_circuit_reset,
    rotate_credential,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/webhook-ops", tags=["webhook-ops"])


# ── IP allowlist ────────────────────────────────────────────────────────────

@router.get("/ip-allowlist", response_model=list[WebhookIpAllowlistOut])
async def list_ip_allowlist(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str | None = Query(None),
):
    q = select(WebhookIpAllowlist).where(WebhookIpAllowlist.workspace_id == workspace_id)
    if provider:
        q = q.where(WebhookIpAllowlist.provider == provider)
    return (await db.execute(q.order_by(WebhookIpAllowlist.provider, WebhookIpAllowlist.cidr))).scalars().all()


@router.post("/ip-allowlist", response_model=WebhookIpAllowlistOut, status_code=201)
async def create_ip_allowlist(
    workspace_id: UUID,
    body: WebhookIpAllowlistCreate,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = WebhookIpAllowlist(workspace_id=workspace_id, **body.model_dump())
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


@router.delete("/ip-allowlist/{row_id}", status_code=204)
async def delete_ip_allowlist(
    workspace_id: UUID,
    row_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    row = await db.get(WebhookIpAllowlist, row_id)
    if not row or row.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Row not found")
    await db.delete(row)


# ── Circuit breaker ─────────────────────────────────────────────────────────

@router.get("/circuits", response_model=list[ChannelCircuitOut])
async def list_circuits(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(ChannelCircuitState)
        .where(ChannelCircuitState.workspace_id == workspace_id)
        .order_by(ChannelCircuitState.state.desc())
    )
    return (await db.execute(q)).scalars().all()


@router.post("/circuits/{channel_account_id}/reset", status_code=204)
async def reset_circuit(
    workspace_id: UUID,
    channel_account_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await db.get(ChannelAccount, channel_account_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    await manual_circuit_reset(channel_account_id)


# ── Secret rotation ─────────────────────────────────────────────────────────

@router.post(
    "/channels/{channel_account_id}/rotate-credential",
    response_model=CredentialRotationOut,
)
async def rotate_channel_credential(
    workspace_id: UUID,
    channel_account_id: UUID,
    body: CredentialRotateRequest,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await db.get(ChannelAccount, channel_account_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account_id,
            ChannelCredential.credential_type == body.credential_type,
        )
    )
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    rotated = await rotate_credential(
        db, credential=credential, new_payload=body.payload, grace_hours=body.grace_hours
    )
    return CredentialRotationOut(rotated=True, grace_until=rotated.grace_until)


@router.post(
    "/channels/{channel_account_id}/finalize-rotation",
    status_code=204,
)
async def finalize_channel_rotation(
    workspace_id: UUID,
    channel_account_id: UUID,
    credential_type: str,
    current_user: Annotated[User, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    account = await db.get(ChannelAccount, channel_account_id)
    if not account or account.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Channel not found")
    result = await db.execute(
        select(ChannelCredential).where(
            ChannelCredential.channel_account_id == channel_account_id,
            ChannelCredential.credential_type == credential_type,
        )
    )
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    await finalize_rotation(db, credential)


# ── Attempts / latency ─────────────────────────────────────────────────────

@router.get(
    "/events/{event_id}/attempts",
    response_model=list[WebhookAttemptOut],
)
async def list_attempts(
    workspace_id: UUID,
    event_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.models.webhook import WebhookEvent

    event = await db.get(WebhookEvent, event_id)
    if not event or event.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Event not found")
    q = (
        select(WebhookEventAttempt)
        .where(WebhookEventAttempt.webhook_event_id == event_id)
        .order_by(WebhookEventAttempt.attempt.asc())
    )
    return (await db.execute(q)).scalars().all()


@router.get("/latency", response_model=LatencyStats)
async def latency_stats(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(require_roles("admin", "supervisor"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    window_minutes: int = Query(60, ge=1, le=24 * 60),
):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    from app.models.webhook import WebhookEvent

    q = (
        select(WebhookEventAttempt.latency_ms)
        .join(WebhookEvent, WebhookEvent.id == WebhookEventAttempt.webhook_event_id)
        .where(
            WebhookEvent.workspace_id == workspace_id,
            WebhookEventAttempt.created_at >= cutoff,
            WebhookEventAttempt.latency_ms.is_not(None),
        )
    )
    rows = [r[0] for r in (await db.execute(q)).all() if r[0] is not None]
    if not rows:
        return LatencyStats(window_minutes=window_minutes, sample_size=0,
                            p50_ms=None, p95_ms=None, p99_ms=None, avg_ms=None, max_ms=None)
    rows.sort()
    n = len(rows)

    def _percentile(p: float) -> float:
        # nearest-rank
        rank = max(1, min(n, int(round(p / 100 * n))))
        return float(rows[rank - 1])

    return LatencyStats(
        window_minutes=window_minutes,
        sample_size=n,
        p50_ms=_percentile(50),
        p95_ms=_percentile(95),
        p99_ms=_percentile(99),
        avg_ms=round(sum(rows) / n, 2),
        max_ms=max(rows),
    )
