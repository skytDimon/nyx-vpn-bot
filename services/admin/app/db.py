from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import get_database_url


@dataclass(frozen=True)
class Page:
    items: list[dict]
    total: int
    limit: int
    offset: int


def _connect():
    return psycopg2.connect(get_database_url())


def fetch_users(search: str | None, limit: int, offset: int) -> Page:
    query = """
        SELECT tg_id, username, balance, referral_balance, created_at
        FROM users
        {where}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    count_query = "SELECT COUNT(*) FROM users {where}"
    params: list[Any] = []

    where = ""
    if search:
        if search.isdigit():
            where = "WHERE tg_id = %s OR username ILIKE %s"
            params.extend([int(search), f"%{search}%"])
        else:
            where = "WHERE username ILIKE %s"
            params.append(f"%{search}%")

    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(count_query.format(where=where), params)
            total = int(cur.fetchone()["count"])
            cur.execute(query.format(where=where), params + [limit, offset])
            rows = list(cur.fetchall())
    return Page(items=rows, total=total, limit=limit, offset=offset)


def get_user(tg_id: int) -> dict | None:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tg_id, username, balance, referral_balance, created_at
                FROM users
                WHERE tg_id = %s
                """,
                (tg_id,),
            )
            return cur.fetchone()


def update_user(
    tg_id: int, username: str | None, balance: int, referral_balance: int
) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET username = %s,
                    balance = %s,
                    referral_balance = %s
                WHERE tg_id = %s
                """,
                (username, balance, referral_balance, tg_id),
            )


def delete_user(tg_id: int) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM subscriptions WHERE tg_id = %s", (tg_id,))
            cur.execute("DELETE FROM users WHERE tg_id = %s", (tg_id,))


def fetch_subscriptions(limit: int, offset: int) -> Page:
    query = """
        SELECT tg_id, start_at, end_at, subscription_link, updated_at
        FROM subscriptions
        ORDER BY updated_at DESC
        LIMIT %s OFFSET %s
    """
    count_query = "SELECT COUNT(*) FROM subscriptions"

    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(count_query)
            total = int(cur.fetchone()["count"])
            cur.execute(query, (limit, offset))
            rows = list(cur.fetchall())
    return Page(items=rows, total=total, limit=limit, offset=offset)


def get_subscription(tg_id: int) -> dict | None:
    with _connect() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tg_id, start_at, end_at, subscription_link, instructions, updated_at
                FROM subscriptions
                WHERE tg_id = %s
                """,
                (tg_id,),
            )
            return cur.fetchone()


def update_subscription(
    tg_id: int,
    start_at: datetime | None,
    end_at: datetime | None,
    subscription_link: str | None,
    instructions: str | None,
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
                    updated_at = NOW()
                WHERE tg_id = %s
                """,
                (start_at, end_at, subscription_link, instructions, tg_id),
            )
