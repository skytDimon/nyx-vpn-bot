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
    country: str = "fi"


def get_bot_token() -> str:
    return _require("BOT_TOKEN")


def get_database_url() -> str:
    return _require("DATABASE_URL")


def get_redis_url() -> str:
    load_env()
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_xui_settings(country: str = "fi") -> XuiSettings:
    load_env()
    prefix = "NL_" if country == "nl" else ""
    base_url = _require(f"{prefix}XUI_URL")
    username = _require(f"{prefix}XUI_USERNAME")
    password = _require(f"{prefix}XUI_PASSWORD")
    inbound_id = int(_require(f"{prefix}XUI_INBOUND_ID"))
    sub_url = os.getenv(f"{prefix}XUI_SUB_URL")
    return XuiSettings(
        base_url=base_url,
        username=username,
        password=password,
        inbound_id=inbound_id,
        sub_url=sub_url,
        country=country,
    )


def get_sub_public_base(country: str = "fi") -> str:
    load_env()
    prefix = "NL_" if country == "nl" else ""
    base = os.getenv(f"{prefix}SUB_PUBLIC_BASE")
    if base:
        return base.rstrip("/")
    sub_url = os.getenv(f"{prefix}XUI_SUB_URL")
    if sub_url:
        return f"{sub_url.rstrip('/')}/sub"
    raise RuntimeError("SUB_PUBLIC_BASE or XUI_SUB_URL is not set")


def get_sub_landing_base(country: str = "fi") -> str | None:
    load_env()
    prefix = "NL_" if country == "nl" else ""
    base = os.getenv(f"{prefix}SUB_LANDING_BASE")
    if not base:
        return None
    return base.rstrip("/")


def get_required_channel_id() -> int:
    load_env()
    value = os.getenv("REQUIRED_CHANNEL_ID", "-10038773344684")
    return int(value)


def get_required_channel_url() -> str | None:
    load_env()
    value = os.getenv("REQUIRED_CHANNEL_URL")
    if not value:
        return None
    return value.strip()
