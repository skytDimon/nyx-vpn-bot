from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

from app.config import get_xui_settings


@dataclass
class XuiConfig:
    base_url: str
    base_path: str
    sub_url: str | None
    username: str
    password: str
    inbound_id: int


class XuiClient:
    def __init__(self, config: XuiConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            follow_redirects=True,
            timeout=httpx.Timeout(15.0, connect=10.0),
        )

    @classmethod
    def from_env(cls) -> "XuiClient":
        settings = get_xui_settings()
        base_url = settings.base_url
        username = settings.username
        password = settings.password
        inbound_id = settings.inbound_id
        sub_url = settings.sub_url
        parsed = urlsplit(base_url)
        base_path = parsed.path.rstrip("/")
        if parsed.scheme and parsed.netloc:
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        return cls(
            XuiConfig(
                base_url=base_url.rstrip("/"),
                base_path=base_path,
                sub_url=sub_url.rstrip("/") if sub_url else None,
                username=username,
                password=password,
                inbound_id=inbound_id,
            )
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def login(self) -> None:
        response = await self._client.post(
            f"{self._config.base_path}/login",
            data={"username": self._config.username, "password": self._config.password},
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise RuntimeError("XUI login failed")

    async def add_client(self, email: str, days: int = 30) -> str:
        expire_at = datetime.utcnow() + timedelta(days=days)
        expiry_time = int(expire_at.timestamp() * 1000)
        client_id = str(uuid4())
        sub_id = uuid4().hex
        settings = {
            "clients": [
                {
                    "id": client_id,
                    "email": email,
                    "enable": True,
                    "expiryTime": expiry_time,
                    "totalGB": 0,
                    "limitIp": 0,
                    "subId": sub_id,
                }
            ]
        }
        payload = {"id": self._config.inbound_id, "settings": json.dumps(settings)}
        paths = [
            f"{self._config.base_path}/panel/inbound/addClient",
            f"{self._config.base_path}/panel/inbounds/addClient",
            f"{self._config.base_path}/api/inbound/addClient",
            f"{self._config.base_path}/panel/api/inbounds/addClient",
            f"{self._config.base_path}/panel/api/inbound/addClient",
        ]
        last_error: str | None = None
        for path in paths:
            response = await self._client.post(path, data=payload)
            if response.status_code == 404:
                last_error = f"404 on {path}"
                continue
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                message = data.get("msg") or "XUI addClient failed"
                raise RuntimeError(message)
            return sub_id
        raise RuntimeError(f"XUI addClient endpoint not found: {last_error}")

    def subscription_link(self, sub_id: str) -> str:
        if self._config.sub_url:
            return f"{self._config.sub_url}/sub/{sub_id}"
        return f"{self._config.base_url}{self._config.base_path}/sub/{sub_id}"

    async def get_client_subscription(self, email: str) -> tuple[str, datetime] | None:
        paths = [
            f"{self._config.base_path}/panel/api/inbounds/list",
            f"{self._config.base_path}/panel/api/inbound/list",
            f"{self._config.base_path}/panel/inbounds/list",
            f"{self._config.base_path}/panel/inbound/list",
            f"{self._config.base_path}/api/inbounds/list",
        ]
        last_error: str | None = None
        for path in paths:
            response = await self._client.get(path)
            if response.status_code == 404:
                last_error = f"404 on {path}"
                continue
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                raise RuntimeError("XUI inbounds list failed")
            obj = data.get("obj") or data.get("data") or []
            if isinstance(obj, dict):
                obj = obj.get("list") or obj.get("items") or []
            for inbound in obj:
                if inbound.get("id") != self._config.inbound_id:
                    continue
                settings = inbound.get("settings")
                if isinstance(settings, str):
                    try:
                        settings = json.loads(settings)
                    except json.JSONDecodeError:
                        settings = None
                if not isinstance(settings, dict):
                    continue
                clients = settings.get("clients", [])
                for client in clients:
                    if client.get("email") != email:
                        continue
                    sub_id = client.get("subId") or client.get("sub_id")
                    expiry_time = client.get("expiryTime") or 0
                    if not sub_id or not expiry_time:
                        return None
                    end_at = datetime.fromtimestamp(
                        int(expiry_time) / 1000, tz=timezone.utc
                    )
                    return sub_id, end_at
            return None
        raise RuntimeError(f"XUI inbounds list endpoint not found: {last_error}")
