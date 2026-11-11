"""Run async worker code from sync Celery tasks without leaking event-loop state."""
from __future__ import annotations

import asyncio
from typing import Awaitable, TypeVar

T = TypeVar("T")


async def _run_with_cleanup(coro: Awaitable[T]) -> T:
    try:
        return await coro
    finally:
        from app.core.database import engine
        from app.core.redis import close_redis

        await close_redis()
        await engine.dispose()


def run_async(coro: Awaitable[T]) -> T:
    return asyncio.run(_run_with_cleanup(coro))
