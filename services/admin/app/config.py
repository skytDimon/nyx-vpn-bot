from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

_ENV_LOADED = False


def load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    load_dotenv(find_dotenv())
    _ENV_LOADED = True


def _require(name: str) -> str:
    load_env()
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def get_admin_user() -> str:
    load_env()
    return os.getenv("ADMIN_USER", "admin")


def get_admin_pass() -> str:
    load_env()
    return os.getenv("ADMIN_PASS", "Admin112008")


def get_database_url() -> str:
    return _require("DATABASE_URL")


def get_bot_username() -> str:
    load_env()
    return os.getenv("BOT_USERNAME", "testnyxvpnbot")


@dataclass
class XuiSettings:
    base_url: str
    username: str
    password: str
    inbound_ids: list[int]


def get_xui_settings() -> XuiSettings | None:
    """Панель для живой сверки кабинета. Нет XUI_URL — вернём None (сверка пропускается)."""
    load_env()
    base_url = os.getenv("XUI_URL")
    if not base_url:
        return None
    username = os.getenv("XUI_USERNAME", "")
    password = os.getenv("XUI_PASSWORD", "")
    inbound_ids = [
        int(x.strip())
        for x in os.getenv("XUI_INBOUND_IDS", "").split(",")
        if x.strip()
    ]
    return XuiSettings(
        base_url=base_url,
        username=username,
        password=password,
        inbound_ids=inbound_ids,
    )
