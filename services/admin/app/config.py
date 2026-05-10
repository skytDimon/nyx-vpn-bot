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


def get_admin_user() -> str:
    load_env()
    return os.getenv("ADMIN_USER", "admin")


def get_admin_pass() -> str:
    load_env()
    return os.getenv("ADMIN_PASS", "Admin112008")


def get_database_url() -> str:
    return _require("DATABASE_URL")
