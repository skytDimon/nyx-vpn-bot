from __future__ import annotations

import json
import os
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
import psycopg2
from psycopg2.extras import RealDictCursor
import redis

from app.config import get_database_url, get_redis_url

logger = logging.getLogger(__name__)


def _connect():
    dsn = get_database_url()
    return psycopg2.connect(dsn)


def _redis() -> redis.Redis:
    url = get_redis_url()
    return redis.Redis.from_url(url, decode_responses=True)


def init_db() -> None:
    _apply_migrations()


def _apply_migrations() -> None:
    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    if not alembic_ini.exists():
        return
    alembic_cfg = Config(str(alembic_ini))
    command.upgrade(alembic_cfg, "head")


def ensure_user(tg_id: int, username: str | None) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (tg_id, username)
                VALUES (%s, %s)
                ON CONFLICT (tg_id)
                DO UPDATE SET username = COALESCE(EXCLUDED.username, users.username)
                """,
                (tg_id, username),
            )


def is_trial_used(tg_id: int) -> bool:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT trial_used FROM users WHERE tg_id = %s",
                (tg_id,),
            )
            row = cur.fetchone()
            if not row:
                return False
            return bool(row["trial_used"])


def set_trial_used(tg_id: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET trial_used = TRUE WHERE tg_id = %s",
                (tg_id,),
            )


def set_subscription(
    tg_id: int,
    start_at: datetime,
    end_at: datetime,
    subscription_link: str,
    instructions: str,
    country: str = "nl",
    client_uuid: str | None = None,
    sub_id: str | None = None,
) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscriptions (tg_id, start_at, end_at, subscription_link, instructions, country, client_uuid, sub_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tg_id)
                DO UPDATE SET start_at = EXCLUDED.start_at,
                              end_at = EXCLUDED.end_at,
                              subscription_link = EXCLUDED.subscription_link,
                              instructions = EXCLUDED.instructions,
                              country = EXCLUDED.country,
                              client_uuid = EXCLUDED.client_uuid,
                              sub_id = EXCLUDED.sub_id,
                              updated_at = NOW()
                """,
                (tg_id, start_at, end_at, subscription_link, instructions, country, client_uuid, sub_id),
            )
    _cache_set_subscription(
        tg_id, start_at, end_at, subscription_link, instructions, country, client_uuid, sub_id
    )


def get_subscription(tg_id: int) -> tuple[datetime | None, datetime | None]:
    cached = _cache_get_subscription(tg_id)
    if cached:
        return cached["start_at"], cached["end_at"]
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT start_at, end_at, subscription_link, instructions, country, client_uuid, sub_id
                FROM subscriptions WHERE tg_id = %s
                """,
                (tg_id,),
            )
            row = cur.fetchone()
            if not row:
                return None, None
            start_at = row["start_at"]
            end_at = row["end_at"]
            end_at = _normalize_dt(end_at)
            if end_at and end_at < datetime.now(timezone.utc):
                clear_subscription(tg_id)
                return None, None
            _cache_set_subscription(
                tg_id,
                start_at,
                end_at,
                row["subscription_link"],
                row["instructions"],
                row.get("country") or "nl",
                row.get("client_uuid"),
                row.get("sub_id"),
            )
            return start_at, end_at


def get_vpn_data(tg_id: int) -> tuple[str | None, str | None]:
    cached = _cache_get_subscription(tg_id)
    if cached:
        return cached["subscription_link"], cached["instructions"]
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT subscription_link, instructions, end_at, country, client_uuid, sub_id
                FROM subscriptions WHERE tg_id = %s
                """,
                (tg_id,),
            )
            row = cur.fetchone()
            if not row:
                return None, None
            end_at = row["end_at"]
            end_at = _normalize_dt(end_at)
            if end_at and end_at < datetime.now(timezone.utc):
                clear_subscription(tg_id)
                return None, None
            return row["subscription_link"], row["instructions"]


def get_subscription_meta(tg_id: int) -> dict | None:
    cached = _cache_get_subscription(tg_id)
    if cached:
        return {
            "start_at": cached["start_at"],
            "end_at": cached["end_at"],
            "subscription_link": cached["subscription_link"],
            "instructions": cached["instructions"],
            "country": cached.get("country") or "nl",
            "client_uuid": cached.get("client_uuid"),
            "sub_id": cached.get("sub_id"),
        }
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT start_at, end_at, subscription_link, instructions, country, client_uuid, sub_id
                FROM subscriptions WHERE tg_id = %s
                """,
                (tg_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            end_at = _normalize_dt(row["end_at"])
            if end_at and end_at < datetime.now(timezone.utc):
                clear_subscription(tg_id)
                return None
            _cache_set_subscription(
                tg_id,
                row["start_at"],
                row["end_at"],
                row["subscription_link"],
                row["instructions"],
                row.get("country") or "nl",
                row.get("client_uuid"),
                row.get("sub_id"),
            )
            return dict(row)


def clear_subscription(tg_id: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM subscriptions WHERE tg_id = %s", (tg_id,))
    _cache_clear_subscription(tg_id)


def purge_expired_subscriptions() -> int:
    grace_hours = int(os.getenv("SUBSCRIPTION_PURGE_GRACE_HOURS", "24"))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=grace_hours)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM subscriptions WHERE end_at IS NOT NULL AND end_at < %s",
                (cutoff,),
            )
            deleted = cur.rowcount
    return deleted


def fetch_subscription_end_dates() -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT tg_id, end_at FROM subscriptions WHERE end_at IS NOT NULL"
            )
            return list(cur.fetchall())


def fetch_active_subscriptions_with_users(country: str | None = None) -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if country:
                cur.execute(
                    """
                    SELECT s.tg_id, s.start_at, s.end_at, u.username, s.country
                    FROM subscriptions s
                    LEFT JOIN users u ON u.tg_id = s.tg_id
                    WHERE s.end_at IS NOT NULL AND s.end_at > NOW() AND s.country = %s
                    """,
                    (country,),
                )
            else:
                cur.execute(
                    """
                    SELECT s.tg_id, s.start_at, s.end_at, u.username, s.country
                    FROM subscriptions s
                    LEFT JOIN users u ON u.tg_id = s.tg_id
                    WHERE s.end_at IS NOT NULL AND s.end_at > NOW()
                    """
                )
            return list(cur.fetchall())


def fetch_all_user_ids() -> list[int]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tg_id FROM users")
            return [row[0] for row in cur.fetchall()]


def fetch_users_with_subscription_links(
    min_days: int = 3, max_days: int = 30
) -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT s.tg_id, s.subscription_link
                FROM subscriptions s
                WHERE s.subscription_link IS NOT NULL
                  AND s.end_at IS NOT NULL
                  AND s.start_at IS NOT NULL
                  AND s.end_at > NOW()
                  AND (s.end_at - s.start_at) >= (%s || ' days')::interval
                  AND (s.end_at - s.start_at) < (%s || ' days')::interval
                """,
                (min_days, max_days),
            )
            return list(cur.fetchall())


def update_subscription_record(
    tg_id: int,
    start_at: datetime | None,
    end_at: datetime | None,
    subscription_link: str | None,
    instructions: str | None,
    country: str | None = None,
) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE subscriptions
                SET start_at = %s,
                    end_at = %s,
                    subscription_link = %s,
                    instructions = %s,
                    country = COALESCE(%s, country),
                    updated_at = NOW()
                WHERE tg_id = %s
                """,
                (start_at, end_at, subscription_link, instructions, country, tg_id),
            )
    _cache_set_subscription(
        tg_id, start_at, end_at, subscription_link, instructions, country
    )


def _cache_key(tg_id: int) -> str:
    return f"subscription:{tg_id}"


def _cache_set_subscription(
    tg_id: int,
    start_at: datetime | None,
    end_at: datetime | None,
    subscription_link: str | None,
    instructions: str | None,
    country: str | None = None,
    client_uuid: str | None = None,
    sub_id: str | None = None,
) -> None:
    if not end_at:
        return
    end_at = _normalize_dt(end_at)
    if not end_at:
        return
    ttl = int((end_at - datetime.now(timezone.utc)).total_seconds())
    if ttl <= 0:
        return
    payload = json.dumps(
        {
            "start_at": start_at.isoformat() if start_at else None,
            "end_at": end_at.isoformat() if end_at else None,
            "subscription_link": subscription_link,
            "instructions": instructions,
            "country": country,
            "client_uuid": client_uuid,
            "sub_id": sub_id,
        }
    )
    try:
        _redis().setex(_cache_key(tg_id), ttl, payload)
    except redis.RedisError:
        return


def _cache_get_subscription(tg_id: int) -> dict | None:
    try:
        raw = _redis().get(_cache_key(tg_id))
    except redis.RedisError:
        return None
    if not raw:
        return None
    data = json.loads(raw)
    start_at = (
        datetime.fromisoformat(data["start_at"]) if data.get("start_at") else None
    )
    end_at = datetime.fromisoformat(data["end_at"]) if data.get("end_at") else None
    end_at = _normalize_dt(end_at)
    if end_at and end_at < datetime.now(timezone.utc):
        _cache_clear_subscription(tg_id)
        return None
    return {
        "start_at": _normalize_dt(start_at),
        "end_at": end_at,
        "subscription_link": data.get("subscription_link"),
        "instructions": data.get("instructions"),
        "country": data.get("country") or "nl",
        "client_uuid": data.get("client_uuid"),
        "sub_id": data.get("sub_id"),
    }


def _cache_clear_subscription(tg_id: int) -> None:
    try:
        _redis().delete(_cache_key(tg_id))
    except redis.RedisError:
        return


def _normalize_dt(value: datetime | None) -> datetime | None:
    if not value:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
