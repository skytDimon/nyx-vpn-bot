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


@dataclass(frozen=True)
class XuiSettings:
    base_url: str
    username: str
    password: str
    inbound_id: int
    sub_url: str | None


def get_bot_token() -> str:
    return _require("BOT_TOKEN")


def get_database_url() -> str:
    return _require("DATABASE_URL")


def get_redis_url() -> str:
    load_env()
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_xui_settings() -> XuiSettings:
    base_url = _require("XUI_URL")
    username = _require("XUI_USERNAME")
    password = _require("XUI_PASSWORD")
    inbound_id = int(_require("XUI_INBOUND_ID"))
    load_env()
    sub_url = os.getenv("XUI_SUB_URL")
    return XuiSettings(
        base_url=base_url,
        username=username,
        password=password,
        inbound_id=inbound_id,
        sub_url=sub_url,
    )
