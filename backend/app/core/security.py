import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


# ── Webhook HMAC validation ───────────────────────────────────────────────────

def verify_hmac_sha256(secret: str, payload: bytes, signature: str) -> bool:
    """Constant-time HMAC-SHA256 comparison."""
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    provided = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)


def verify_webhook_timestamp(ts: int | str, max_age_seconds: int = 300) -> bool:
    """Reject webhooks older than max_age_seconds (replay attack prevention)."""
    try:
        age = time.time() - int(ts)
        return 0 <= age <= max_age_seconds
    except (ValueError, TypeError):
        return False


def webhook_replay_key(provider: str, signature: str) -> str:
    digest = hashlib.sha256(f"{provider}:{signature}".encode()).hexdigest()
    return f"webhook:replay:{digest}"


async def is_webhook_signature_registered(redis, provider: str, signature: str) -> bool:
    if not signature:
        return False
    return bool(await redis.exists(webhook_replay_key(provider, signature)))


async def register_webhook_signature(redis, provider: str, signature: str, ttl_seconds: int = 300) -> bool:
    """Return False when a webhook signature was already seen in the TTL window."""
    if not signature:
        return False
    key = webhook_replay_key(provider, signature)
    return bool(await redis.set(key, "1", ex=ttl_seconds, nx=True))
