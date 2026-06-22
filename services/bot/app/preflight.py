from __future__ import annotations

import asyncio
import logging
import urllib.parse

import psycopg2
import redis

from app.config import get_database_url, get_redis_url, get_xui_settings

logger = logging.getLogger(__name__)


def _check_db() -> None:
    dsn = get_database_url()
    conn = psycopg2.connect(dsn, connect_timeout=5)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    finally:
        conn.close()


def _check_redis() -> None:
    url = get_redis_url()
    client = redis.Redis.from_url(url, decode_responses=True, socket_timeout=5)
    try:
        client.ping()
    except redis.RedisError as exc:
        raise RuntimeError(
            "Redis unavailable. Ensure Redis is running and REDIS_URL is correct. "
            "Example: redis://localhost:6379/0"
        ) from exc


async def _check_xui() -> None:
    import httpx
    settings = get_xui_settings()
    parsed = urllib.parse.urlsplit(settings.base_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    base_path = parsed.path.rstrip("/")
    login_url = f"{base_url}{base_path}/login"
    client = httpx.AsyncClient(verify=False, timeout=10.0)
    try:
        resp = await client.post(
            login_url,
            data={"username": settings.username, "password": settings.password},
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                logger.info("XUI panel reachable and login successful")
                return
        raise RuntimeError(f"XUI login failed: {resp.status_code} {resp.text}")
    except httpx.ConnectError as exc:
        raise RuntimeError(f"XUI panel unreachable: {settings.base_url}") from exc
    finally:
        await client.aclose()


async def run_preflight() -> None:
    await asyncio.to_thread(_check_db)
    await asyncio.to_thread(_check_redis)
    await _check_xui()
