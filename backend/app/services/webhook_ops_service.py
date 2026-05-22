"""Stage 4 Tier 2 — operational helpers around webhook ingestion.

- Secret rotation: stash previous_payload + grace_until on ChannelCredential
  and accept either old or new HMAC during the grace window.
- IP allowlist: enforce per (workspace, provider) when at least one row exists.
- Circuit breaker: trip a channel after N consecutive failures; reject inbound
  webhooks while open; auto half-open after a cool-off; success closes.
- Attempt log: append a WebhookEventAttempt for every processing try, with a
  payload hash so the UI can show "payload changed across attempts".
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.encryption import decrypt_payload, encrypt_payload
from app.core.security import verify_hmac_sha256
from app.models.channel import ChannelCredential
from app.models.enums import CircuitState, WebhookEventStatus
from app.models.webhook_ops import (
    ChannelCircuitState,
    WebhookEventAttempt,
    WebhookIpAllowlist,
)

logger = logging.getLogger(__name__)

# Circuit breaker tuning
CIRCUIT_FAILURE_THRESHOLD = 10            # consecutive failures to open
CIRCUIT_OPEN_DURATION_SECONDS = 5 * 60    # cool-off before half-open probe


# ── Secret rotation ─────────────────────────────────────────────────────────

def verify_hmac_with_rotation(
    credential: ChannelCredential,
    secret_field: str,
    raw_body: bytes,
    signature: str,
) -> tuple[bool, str | None]:
    """Verify HMAC accepting both current and previous (during grace) secret.

    Returns (ok, used_secret_label) where used_secret_label is "current" or
    "previous" or None.
    """
    try:
        current_payload = decrypt_payload(credential.encrypted_payload) or {}
    except Exception:  # noqa: BLE001
        current_payload = {}
    current_secret = current_payload.get(secret_field)
    if current_secret and verify_hmac_sha256(current_secret, raw_body, signature):
        return True, "current"

    # Previous secret, only if grace window is still open
    if (
        credential.previous_payload
        and credential.grace_until
        and credential.grace_until > datetime.now(timezone.utc)
    ):
        try:
            prev = decrypt_payload(credential.previous_payload) or {}
        except Exception:  # noqa: BLE001
            prev = {}
        previous_secret = prev.get(secret_field)
        if previous_secret and verify_hmac_sha256(previous_secret, raw_body, signature):
            return True, "previous"
    return False, None


async def rotate_credential(
    db: AsyncSession,
    *,
    credential: ChannelCredential,
    new_payload: dict[str, Any],
    grace_hours: int = 24,
) -> ChannelCredential:
    """Move the current encrypted payload into previous_payload, install the
    new one as encrypted_payload and set grace_until."""
    credential.previous_payload = credential.encrypted_payload
    credential.encrypted_payload = encrypt_payload(new_payload)
    credential.grace_until = datetime.now(timezone.utc) + timedelta(hours=grace_hours)
    credential.rotated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(credential)
    return credential


async def finalize_rotation(db: AsyncSession, credential: ChannelCredential) -> None:
    """Drop the previous_payload — used by an admin to short-circuit the grace
    window once they're confident."""
    credential.previous_payload = None
    credential.grace_until = None
    await db.flush()


# ── IP allowlist ────────────────────────────────────────────────────────────

async def check_ip_allowed(
    db: AsyncSession, workspace_id: UUID | None, provider: str, ip: str | None
) -> bool:
    if workspace_id is None or ip is None:
        return True
    result = await db.execute(
        select(WebhookIpAllowlist).where(
            WebhookIpAllowlist.workspace_id == workspace_id,
            WebhookIpAllowlist.provider == provider,
        )
    )
    cidrs = [row.cidr for row in result.scalars().all()]
    if not cidrs:
        return True  # no policy configured == allow all
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for cidr in cidrs:
        try:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


# ── Circuit breaker ─────────────────────────────────────────────────────────

async def _get_or_create_circuit(
    db: AsyncSession, workspace_id: UUID, channel_account_id: UUID
) -> ChannelCircuitState:
    result = await db.execute(
        select(ChannelCircuitState).where(
            ChannelCircuitState.channel_account_id == channel_account_id
        )
    )
    circuit = result.scalar_one_or_none()
    if circuit:
        return circuit
    circuit = ChannelCircuitState(
        workspace_id=workspace_id,
        channel_account_id=channel_account_id,
    )
    db.add(circuit)
    await db.flush()
    return circuit


async def is_circuit_open(
    db: AsyncSession, workspace_id: UUID, channel_account_id: UUID
) -> bool:
    """Returns True only when traffic should be rejected immediately.

    `open` rejects; `half_open` allows a single probe; `closed` is normal.
    """
    result = await db.execute(
        select(ChannelCircuitState).where(
            ChannelCircuitState.channel_account_id == channel_account_id
        )
    )
    circuit = result.scalar_one_or_none()
    if not circuit:
        return False
    if circuit.state == CircuitState.open:
        if circuit.next_probe_at and circuit.next_probe_at <= datetime.now(timezone.utc):
            circuit.state = CircuitState.half_open
            await db.flush()
            return False
        return True
    return False


async def record_circuit_failure(
    workspace_id: UUID, channel_account_id: UUID, error_message: str | None = None
) -> None:
    try:
        async with AsyncSessionLocal() as db:
            circuit = await _get_or_create_circuit(db, workspace_id, channel_account_id)
            circuit.failure_count += 1
            circuit.last_failure_at = datetime.now(timezone.utc)
            circuit.last_error_message = error_message
            if circuit.state == CircuitState.half_open:
                # probe failed → reopen with backoff
                circuit.state = CircuitState.open
                circuit.opened_at = datetime.now(timezone.utc)
                circuit.next_probe_at = datetime.now(timezone.utc) + timedelta(
                    seconds=CIRCUIT_OPEN_DURATION_SECONDS
                )
            elif (
                circuit.state == CircuitState.closed
                and circuit.failure_count >= CIRCUIT_FAILURE_THRESHOLD
            ):
                circuit.state = CircuitState.open
                circuit.opened_at = datetime.now(timezone.utc)
                circuit.next_probe_at = datetime.now(timezone.utc) + timedelta(
                    seconds=CIRCUIT_OPEN_DURATION_SECONDS
                )
            await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to record circuit failure for channel %s", channel_account_id)


async def record_circuit_success(workspace_id: UUID, channel_account_id: UUID) -> None:
    try:
        async with AsyncSessionLocal() as db:
            circuit = await _get_or_create_circuit(db, workspace_id, channel_account_id)
            circuit.failure_count = 0
            circuit.last_error_message = None
            if circuit.state != CircuitState.closed:
                circuit.state = CircuitState.closed
                circuit.opened_at = None
                circuit.next_probe_at = None
            await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to record circuit success for channel %s", channel_account_id)


async def manual_circuit_reset(channel_account_id: UUID) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChannelCircuitState).where(
                ChannelCircuitState.channel_account_id == channel_account_id
            )
        )
        circuit = result.scalar_one_or_none()
        if not circuit:
            return
        circuit.state = CircuitState.closed
        circuit.failure_count = 0
        circuit.opened_at = None
        circuit.next_probe_at = None
        circuit.last_error_message = None
        await db.commit()


# ── Attempt log ─────────────────────────────────────────────────────────────

def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


async def record_attempt(
    *,
    webhook_event_id: UUID,
    attempt: int,
    payload: dict[str, Any],
    status: str,
    error_message: str | None,
    latency_ms: int | None,
) -> None:
    try:
        async with AsyncSessionLocal() as db:
            db.add(
                WebhookEventAttempt(
                    webhook_event_id=webhook_event_id,
                    attempt=attempt,
                    payload_hash=payload_hash(payload),
                    payload_snapshot=payload,
                    status=status,
                    error_message=error_message,
                    latency_ms=latency_ms,
                )
            )
            await db.commit()
    except SQLAlchemyError:
        logger.exception("Failed to record webhook attempt for %s", webhook_event_id)
