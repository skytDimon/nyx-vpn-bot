from __future__ import annotations

import os

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


def get_api_key() -> str:
    return _require("API_KEY")


def get_api_base_url() -> str:
    load_env()
    return os.getenv("API_BASE_URL", "https://nyxvpnde.port0.org:8442")


def get_trial_days() -> int:
    load_env()
    return int(os.getenv("TRIAL_DAYS", "3"))


def get_remind_hours_before() -> int:
    load_env()
    return int(os.getenv("REMIND_HOURS_BEFORE", "20"))
