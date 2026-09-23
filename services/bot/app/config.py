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


def get_admin_id() -> int:
    return int(_require("ADMIN_ID"))


def get_sbp_phone_number() -> str:
    return _require("SBP_PHONE_NUMBER")


def get_smtp_settings() -> dict:
    load_env()
    return {
        "host": "smtp.gmail.com",
        "port": 587,
        "login": "dimdimich112008@gmail.com",
        "password": _require("GMAIL_APP_PASSWORD"),
        "to_email": "dimdimich112008@gmail.com",
    }


def get_payment_amount() -> int:
    load_env()
    return int(os.getenv("PAYMENT_AMOUNT", "150"))


def get_payment_days() -> int:
    load_env()
    return int(os.getenv("PAYMENT_DAYS", "30"))


def get_jwt_secret() -> str:
    return _require("JWT_SECRET")


def get_cabinet_url() -> str:
    return _require("CABINET_URL")


@dataclass
class VpnServer:
    name: str
    host: str
    port: int


def get_vpn_servers() -> list[VpnServer]:
    """Parse VPN_SERVERS env var.

    Format: ``name:host:port,name:host:port,...``
    Example: ``🇳🇱 Нидерланды:185.1.2.3:443,🇩🇪 Германия:195.4.5.6:443``

    Falls back to extracting the host from XUI_URL if VPN_SERVERS is not set.
    """
    load_env()
    raw = os.getenv("VPN_SERVERS", "").strip()
    if raw:
        servers: list[VpnServer] = []
        for entry in raw.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.rsplit(":", 2)
            if len(parts) == 3:
                name, host, port_s = parts
                servers.append(VpnServer(name=name.strip(), host=host.strip(), port=int(port_s)))
            elif len(parts) == 2:
                name, host = parts
                servers.append(VpnServer(name=name.strip(), host=host.strip(), port=443))
        return servers

    # Fallback: extract host from XUI_URL
    from urllib.parse import urlsplit

    xui_url = os.getenv("XUI_URL", "")
    if xui_url:
        parsed = urlsplit(xui_url)
        host = parsed.hostname or ""
        port = parsed.port or 443
        if host:
            return [VpnServer(name="VPN Server", host=host, port=port)]
    return []
