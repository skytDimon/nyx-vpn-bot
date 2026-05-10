from __future__ import annotations

import asyncio
import psycopg2
import redis

from app.config import get_database_url, get_redis_url
from app.services.xui_manager import XuiManagerClient


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


async def _check_xui_manager() -> None:
    import logging
    logger = logging.getLogger(__name__)
    client = XuiManagerClient()
    try:
        import httpx
        url = f"{client._base_url}/api/add_client"
        resp = await client._client.get(url, headers={"X-API-Key": client._api_key})
        if resp.status_code == 404:
            logger.warning(
                "X-UI Manager API health check: got 404 (expected). "
                "Base URL is reachable, proceeding."
            )
            return
        if resp.status_code in (401, 403):
            raise RuntimeError(
                "X-UI Manager API: unauthorized. Check API_KEY."
            )
        logger.info("X-UI Manager API reachable (status %s)", resp.status_code)
    except httpx.ConnectError as exc:
        raise RuntimeError(
            "X-UI Manager API unreachable. Check API_BASE_URL."
        ) from exc
    finally:
        await client.close()


async def run_preflight() -> None:
    await asyncio.to_thread(_check_db)
    await asyncio.to_thread(_check_redis)
    await _check_xui_manager()
