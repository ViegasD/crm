"""Helpers to extract trusted request metadata (IP, user agent) behind proxies."""
from fastapi import Request


def client_ip(request: Request) -> str | None:
    """Return the originating client IP, respecting X-Forwarded-For when present.

    The leftmost entry in XFF is the original client; intermediate hops append
    their own address. In production this should run only when the app is
    behind a trusted proxy (Nginx, Traefik, Cloudflare).
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else None


def user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")
