import asyncio
import logging
import math
from datetime import datetime, timezone

from app.config import get_sub_landing_base, get_xui_settings, load_env
from app.services.xui_client import XuiClient
from app.storage import (
    fetch_active_subscriptions_with_users,
    update_subscription_record,
)
from app.vpn_instructions import vpn_instructions


def _email_for_user(tg_id: int, username: str | None) -> str:
    return f"@{username or f'tg_{tg_id}'}"


async def main() -> int:
    load_env()
    landing_base = get_sub_landing_base("nl")
    if not landing_base:
        raise RuntimeError("NL_SUB_LANDING_BASE is not set")
    rows = fetch_active_subscriptions_with_users(country="nl")
    if not rows:
        print("No active subscriptions found.")
        return 0

    now = datetime.now(timezone.utc)
    updated = 0
    skipped = 0

    settings = get_xui_settings("nl")
    xui = XuiClient.from_settings(settings)
    try:
        await xui.login()
        for row in rows:
            tg_id = int(row["tg_id"])
            start_at = row["start_at"]
            end_at = row["end_at"]
            username = row.get("username")
            if not end_at:
                skipped += 1
                continue
            if end_at.tzinfo is None:
                end_at = end_at.replace(tzinfo=timezone.utc)

            email = _email_for_user(tg_id, username)
            try:
                result = await xui.get_client_subscription(email)
            except Exception:
                logging.exception("Failed to fetch client for tg_id=%s", tg_id)
                skipped += 1
                continue

            if result:
                sub_id, _ = result
            else:
                remaining_days = max(
                    1, math.ceil((end_at - now).total_seconds() / 86400)
                )
                try:
                    sub_id = await xui.add_client(email=email, days=remaining_days)
                except Exception:
                    logging.exception("Failed to create client for tg_id=%s", tg_id)
                    skipped += 1
                    continue

            sub_link = f"{landing_base.rstrip('/')}/{sub_id}"
            instructions = vpn_instructions(sub_link, landing=True)
            update_subscription_record(
                tg_id, start_at, end_at, sub_link, instructions, country="nl"
            )
            updated += 1
    finally:
        await xui.close()

    print(f"Updated subscriptions: {updated}. Skipped: {skipped}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
