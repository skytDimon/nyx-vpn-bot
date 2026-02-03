from __future__ import annotations

from datetime import datetime, timedelta, timezone

import redis
from aiogram import Bot

from app.config import get_redis_url
from app.storage import clear_subscription, fetch_subscription_end_dates

THREE_DAYS = timedelta(days=3)
REDIS_TTL_EXTRA = timedelta(days=7)


def _redis() -> redis.Redis:
    return redis.Redis.from_url(get_redis_url(), decode_responses=True)


def _notify_key(prefix: str, tg_id: int, end_at: datetime) -> str:
    return f"notify:{prefix}:{tg_id}:{end_at.isoformat()}"


def _set_notified(key: str, end_at: datetime) -> None:
    ttl = int((end_at + REDIS_TTL_EXTRA - datetime.now(timezone.utc)).total_seconds())
    if ttl <= 0:
        ttl = int(REDIS_TTL_EXTRA.total_seconds())
    _redis().setex(key, ttl, "1")


def _was_notified(key: str) -> bool:
    return _redis().get(key) is not None


async def notify_subscriptions(bot: Bot) -> None:
    now = datetime.now(timezone.utc)
    for row in fetch_subscription_end_dates():
        tg_id = row["tg_id"]
        end_at = row["end_at"]
        if not end_at:
            continue
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=timezone.utc)

        if end_at <= now:
            key = _notify_key("expired", tg_id, end_at)
            if _was_notified(key):
                continue
            try:
                await bot.send_message(
                    tg_id,
                    "⛔️ Подписка завершилась.\n"
                    "Для продления откройте раздел тарифов и выберите оплату.",
                )
            except Exception:
                pass
            _set_notified(key, end_at)
            clear_subscription(tg_id)
            continue

        if end_at - now <= THREE_DAYS:
            key = _notify_key("three_days", tg_id, end_at)
            if _was_notified(key):
                continue
            try:
                await bot.send_message(
                    tg_id,
                    "⏳ До окончания подписки осталось 3 дня.\n"
                    "Продлите доступ заранее, чтобы не потерять VPN.",
                )
            except Exception:
                pass
            _set_notified(key, end_at)
