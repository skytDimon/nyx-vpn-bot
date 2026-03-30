"""Look up a user's VPN subscription in the 3x-ui SQLite database."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from functools import partial

logger = logging.getLogger(__name__)

XUI_DB_PATH = "/etc/x-ui/x-ui.db"
SUB_PAGE_URL = "https://nyxvpnnl.home.kg/index.html"


def _find_sub_id(username: str, db_path: str = XUI_DB_PATH) -> str | None:
    """Synchronous helper that queries the 3x-ui database.

    Searches all ``inbounds`` rows, parses the ``settings`` JSON column and
    looks for a client whose ``email`` matches ``@<username>`` or ``<username>``.

    Returns the ``subId`` string if found, otherwise ``None``.
    """
    email_variants = {f"@{username}", username}

    try:
        con = sqlite3.connect(db_path, timeout=5)
        try:
            cur = con.execute("SELECT settings FROM inbounds")
            for (settings_raw,) in cur.fetchall():
                if not settings_raw:
                    continue
                try:
                    settings = json.loads(settings_raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                for client in settings.get("clients", []):
                    if client.get("email") in email_variants:
                        sub_id = client.get("subId")
                        if sub_id:
                            return sub_id
        finally:
            con.close()
    except sqlite3.Error:
        logger.exception("Failed to read 3x-ui database at %s", db_path)

    return None


async def get_subscription_link(username: str) -> str | None:
    """Return the subscription page URL for *username*, or ``None``.

    The heavy SQLite work is offloaded to a thread via ``run_in_executor``
    so the bot's event-loop stays responsive.
    """
    loop = asyncio.get_running_loop()
    sub_id = await loop.run_in_executor(None, partial(_find_sub_id, username))
    if not sub_id:
        return None
    return f"{SUB_PAGE_URL}?id={sub_id}"
