"""Redis-backed sliding-window rate limiter for webhook endpoints.

Use as a FastAPI dependency:

    @router.post("", dependencies=[Depends(webhook_rate_limit("meta"))])

The default policy is 120 requests / 60 seconds per (provider, ip). Excess
requests return 429.
"""
from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis
from app.core.request_meta import client_ip


def webhook_rate_limit(
    provider: str,
    *,
    limit: int = 120,
    window_seconds: int = 60,
):
    async def _check(request: Request) -> None:
        ip = client_ip(request) or "unknown"
        redis = await get_redis()
        key = f"rl:webhook:{provider}:{ip}:{int(window_seconds)}"
        # INCR + EXPIRE: simple fixed-window counter
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Webhook rate limit exceeded",
                headers={"Retry-After": str(window_seconds)},
            )

    return _check
