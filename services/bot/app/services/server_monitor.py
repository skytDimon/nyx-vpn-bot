"""Server health monitor — TCP-ping VPN servers and cache results in Redis."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

import redis

from app.config import get_redis_url, get_vpn_servers

logger = logging.getLogger(__name__)

REDIS_KEY = "server_status"
REDIS_TTL = 6 * 3600  # 6 hours (slightly longer than 5h check interval)
REFRESH_COOLDOWN = 60  # seconds between manual refreshes


async def tcp_ping(host: str, port: int, timeout: float = 5.0) -> tuple[bool, float | None]:
    """Try to open a TCP connection and measure round-trip time.

    Returns (is_alive, latency_ms).
    """
    start = time.monotonic()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        writer.close()
        await writer.wait_closed()
        return True, round(elapsed_ms, 1)
    except (OSError, asyncio.TimeoutError, Exception) as exc:
        logger.debug("tcp_ping %s:%s failed: %s", host, port, exc)
        return False, None


async def check_all_servers() -> list[dict]:
    """Ping every configured VPN server and save results to Redis.

    Returns the list of status dicts.
    """
    servers = get_vpn_servers()
    if not servers:
        logger.warning("No VPN servers configured (VPN_SERVERS is empty)")
        return []

    results: list[dict] = []
    for srv in servers:
        alive, latency = await tcp_ping(srv.host, srv.port)
        results.append({
            "name": srv.name,
            "alive": alive,
            "latency_ms": latency,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(
            "Server %s (%s:%s): %s %s",
            srv.name,
            srv.host,
            srv.port,
            "UP" if alive else "DOWN",
            f"{latency}ms" if latency else "",
        )

    _save_to_redis(results)
    return results


def _save_to_redis(results: list[dict]) -> None:
    try:
        r = redis.Redis.from_url(get_redis_url(), decode_responses=True)
        r.setex(REDIS_KEY, REDIS_TTL, json.dumps(results, ensure_ascii=False))
    except Exception:
        logger.exception("Failed to save server status to Redis")


def get_cached_status() -> list[dict] | None:
    """Read cached server status from Redis. Returns None if no cache."""
    try:
        r = redis.Redis.from_url(get_redis_url(), decode_responses=True)
        raw = r.get(REDIS_KEY)
        if raw:
            return json.loads(raw)
    except Exception:
        logger.exception("Failed to read server status from Redis")
    return None


def can_refresh() -> bool:
    """Check if enough time has passed since the last refresh (cooldown)."""
    try:
        r = redis.Redis.from_url(get_redis_url(), decode_responses=True)
        return r.set("server_status:cooldown", "1", nx=True, ex=REFRESH_COOLDOWN) is True
    except Exception:
        return True
