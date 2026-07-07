from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import uuid4

import httpx

from app.config import get_xui_settings

logger = logging.getLogger(__name__)


@dataclass
class XuiConfig:
    base_url: str
    base_path: str
    sub_url: str | None
    username: str
    password: str
    inbound_ids: list[int]


class XuiClient:
    def __init__(self, config: XuiConfig):
        self._config = config
        self._csrf_token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            verify=False,
            follow_redirects=True,
            timeout=httpx.Timeout(15.0, connect=10.0),
        )

    @classmethod
    def from_env(cls) -> "XuiClient":
        settings = get_xui_settings()
        return cls.from_settings(settings)

    @classmethod
    def from_settings(cls, settings) -> "XuiClient":
        base_url = settings.base_url
        username = settings.username
        password = settings.password
        inbound_ids = settings.inbound_ids
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
                inbound_ids=inbound_ids,
            )
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def login(self) -> None:
        await self._fetch_csrf_token()
        payload = {"username": self._config.username, "password": self._config.password}
        paths = [
            f"{self._config.base_path}/login",
            f"{self._config.base_path}/login/",
        ]
        last_error: str | None = None
        for path in paths:
            for mode in ("data", "json"):
                response = await self._post(path, payload, mode=mode)
                if response.status_code == 404:
                    last_error = f"404 on {path} ({mode})"
                    continue
                if response.status_code in (401, 403):
                    last_error = f"{response.status_code} on {path} ({mode}): {response.text}"
                    continue
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    logger.info("XUI login successful via %s (%s)", path, mode)
                    return
                last_error = data.get("msg") or f"login failed on {path} ({mode})"
        raise RuntimeError(f"XUI login failed: {last_error}")

    async def add_client(self, email: str, days: int = 3) -> str:
        await self.login()
        expire_at = datetime.now(timezone.utc) + timedelta(days=days)
        expiry_time = int(expire_at.timestamp() * 1000)
        client_id = str(uuid4())
        sub_id = uuid4().hex
        client = {
            "id": client_id,
            "email": email,
            "enable": True,
            "expiryTime": expiry_time,
            "totalGB": 0,
            "limitIp": 0,
            "subId": sub_id,
        }
        if await self._add_client_via_clients_api(client):
            return sub_id

        settings = {
            "clients": [
                client
            ]
        }
        for inbound_id in self._config.inbound_ids:
            payload = {"id": inbound_id, "settings": json.dumps(settings)}
            paths = [
                f"{self._config.base_path}/panel/inbound/addClient",
                f"{self._config.base_path}/panel/inbounds/addClient",
                f"{self._config.base_path}/api/inbound/addClient",
                f"{self._config.base_path}/panel/api/inbounds/addClient",
                f"{self._config.base_path}/panel/api/inbound/addClient",
            ]
            last_error: str | None = None
            for path in paths:
                for mode in ("data", "json"):
                    response = await self._post(path, payload, mode=mode)
                    content_type = response.headers.get("content-type", "")
                    if response.status_code == 404 or "application/json" not in content_type:
                        last_error = f"404 on {path} ({mode})"
                        continue
                    response.raise_for_status()
                    data = response.json()
                    if not data.get("success"):
                        message = data.get("msg") or "XUI addClient failed"
                        last_error = f"{path} ({mode}): {message}"
                        continue
                    logger.info("XUI client added to inbound %s via %s (%s)", inbound_id, path, mode)
                    break
                else:
                    continue
                break
            else:
                raise RuntimeError(
                    f"XUI addClient endpoint not found for inbound {inbound_id}: {last_error}"
                )
        return sub_id

    async def _add_client_via_clients_api(self, client: dict) -> bool:
        path = f"{self._config.base_path}/panel/api/clients/add"
        payload = {"client": client, "inboundIds": self._config.inbound_ids}
        response = await self._post(path, payload, mode="json")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            logger.info(
                "XUI client added via clients API to inbounds %s",
                self._config.inbound_ids,
            )
            return True
        message = data.get("msg") or "XUI clients/add failed"
        raise RuntimeError(f"XUI clients/add failed: {message}")

    def subscription_link(self, sub_id: str) -> str:
        if self._config.sub_url:
            if "{sub_id}" in self._config.sub_url:
                return self._config.sub_url.format(sub_id=sub_id)
            return f"{self._config.sub_url}/sub/{sub_id}"
        return f"{self._config.base_url}{self._config.base_path}/sub/{sub_id}"

    async def _post(self, path: str, payload: dict, mode: str) -> httpx.Response:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" if mode == "data" else "application/json",
            "Referer": f"{self._config.base_url}{self._config.base_path}/",
            "Origin": self._config.base_url,
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        }
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token
        if mode == "json":
            response = await self._client.post(path, json=payload, headers=headers)
        else:
            response = await self._client.post(path, data=payload, headers=headers)
        if response.status_code == 403:
            self._csrf_token = None
            await self._fetch_csrf_token()
            if self._csrf_token:
                headers["X-CSRF-Token"] = self._csrf_token
                if mode == "json":
                    response = await self._client.post(path, json=payload, headers=headers)
                else:
                    response = await self._client.post(path, data=payload, headers=headers)
        return response

    async def _fetch_csrf_token(self) -> None:
        response = await self._client.get(
            f"{self._config.base_path}/csrf-token",
            headers={"X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0"},
        )
        if response.status_code == 404:
            return
        response.raise_for_status()
        data = response.json()
        token = data.get("obj") if data.get("success") else None
        if isinstance(token, str) and token:
            self._csrf_token = token

    async def get_client_subscription(self, email: str) -> tuple[str, datetime] | None:
        await self.login()
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
            content_type = response.headers.get("content-type", "")
            if response.status_code == 404 or "application/json" not in content_type:
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
                if inbound.get("id") not in self._config.inbound_ids:
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
