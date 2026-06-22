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


def get_bot_token() -> str:
    return _require("BOT_TOKEN")


def get_database_url() -> str:
    return _require("DATABASE_URL")


def get_redis_url() -> str:
    load_env()
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_trial_days() -> int:
    load_env()
    return int(os.getenv("TRIAL_DAYS", "3"))


def get_remind_hours_before() -> int:
    load_env()
    return int(os.getenv("REMIND_HOURS_BEFORE", "20"))


@dataclass
class XuiSettings:
    base_url: str
    username: str
    password: str
    inbound_ids: list[int]
    sub_url: str | None


def get_xui_settings() -> XuiSettings:
    load_env()
    base_url = _require("XUI_URL")
    username = _require("XUI_USERNAME")
    password = _require("XUI_PASSWORD")
    inbound_ids = [
        int(x.strip())
        for x in _require("XUI_INBOUND_IDS").split(",")
        if x.strip()
    ]
    sub_url = os.getenv("XUI_SUB_URL")
    return XuiSettings(
        base_url=base_url,
        username=username,
        password=password,
        inbound_ids=inbound_ids,
        sub_url=sub_url,
    )
