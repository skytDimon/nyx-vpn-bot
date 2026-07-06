from __future__ import annotations

import asyncio
import logging

import psycopg2
import redis

from app.config import get_database_url, get_redis_url
from app.services.xui_client import XuiClient

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
    client = XuiClient.from_env()
    try:
        await client.login()
        logger.info("XUI panel reachable and login successful")
    finally:
        await client.close()


async def run_preflight() -> None:
    await asyncio.to_thread(_check_db)
    await asyncio.to_thread(_check_redis)
    await _check_xui()
