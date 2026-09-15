from __future__ import annotations

import json
import logging
from urllib.parse import urlsplit

import httpx

from app.config import XuiSettings, get_xui_settings

logger = logging.getLogger(__name__)


class XuiCabinetChecker:
    """Только чтение: есть ли panel-клиент с таким email на настроенных inbound'ах."""

    def __init__(self, settings: XuiSettings):
        parsed = urlsplit(settings.base_url)
        base_path = parsed.path.rstrip("/")
        base_url = (
            f"{parsed.scheme}://{parsed.netloc}"
            if (parsed.scheme and parsed.netloc)
            else settings.base_url
        )
        self._base_url = base_url.rstrip("/")
        self._base_path = base_path
        self._inbound_ids = settings.inbound_ids
        self._username = settings.username
        self._password = settings.password
        self._csrf: str | None = None
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            verify=False,
            follow_redirects=True,
            timeout=httpx.Timeout(15.0, connect=10.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _fetch_csrf(self) -> None:
        r = await self._client.get(
            f"{self._base_path}/csrf-token",
            headers={"X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0"},
        )
        if r.status_code == 404:
            return
        r.raise_for_status()
        data = r.json()
        tok = data.get("obj") if data.get("success") else None
        if isinstance(tok, str) and tok:
            self._csrf = tok

    async def _post(self, path: str, payload: dict, mode: str) -> httpx.Response:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            if mode == "data"
            else "application/json",
            "Referer": f"{self._base_url}{self._base_path}/",
            "Origin": self._base_url,
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
        }
        if self._csrf:
            headers["X-CSRF-Token"] = self._csrf
        if mode == "json":
            resp = await self._client.post(path, json=payload, headers=headers)
        else:
            resp = await self._client.post(path, data=payload, headers=headers)
        if resp.status_code == 403:
            self._csrf = None
            await self._fetch_csrf()
            if self._csrf:
                headers["X-CSRF-Token"] = self._csrf
                if mode == "json":
                    resp = await self._client.post(path, json=payload, headers=headers)
                else:
                    resp = await self._client.post(path, data=payload, headers=headers)
        return resp

    async def login(self) -> None:
        await self._fetch_csrf()
        payload = {"username": self._username, "password": self._password}
        for path in (f"{self._base_path}/login", f"{self._base_path}/login/"):
            for mode in ("data", "json"):
                r = await self._post(path, payload, mode=mode)
                if r.status_code in (401, 403, 404):
                    continue
                r.raise_for_status()
                data = r.json()
                if data.get("success"):
                    return
        raise RuntimeError("XUI login failed")

    async def client_exists(self, email: str) -> bool | None:
        """
        True — клиент есть на панели (на настроенных inbound'ах).
        False — точно нет.
        None — панель недоступна/endpoint not found (не меняем вывод).
        """
        settings = get_xui_settings()
        if not settings:
            return None
        try:
            await self.login()
        except Exception:
            logger.warning("XUI cabinet check: login failed", exc_info=True)
            return None
        paths = [
            f"{self._base_path}/panel/api/inbounds/list",
            f"{self._base_path}/panel/api/inbound/list",
            f"{self._base_path}/panel/inbounds/list",
            f"{self._base_path}/panel/inbound/list",
            f"{self._base_path}/api/inbounds/list",
        ]
        for path in paths:
            try:
                r = await self._client.get(path)
            except httpx.RequestError:
                return None
            ct = r.headers.get("content-type", "")
            if r.status_code == 404 or "application/json" not in ct:
                continue
            r.raise_for_status()
            data = r.json()
            if not data.get("success"):
                continue
            obj = data.get("obj") or data.get("data") or []
            if isinstance(obj, dict):
                obj = obj.get("list") or obj.get("items") or []
            for inbound in obj:
                if inbound.get("id") not in self._inbound_ids:
                    continue
                settings_raw = inbound.get("settings")
                if isinstance(settings_raw, str):
                    try:
                        settings_raw = json.loads(settings_raw)
                    except json.JSONDecodeError:
                        continue
                if not isinstance(settings_raw, dict):
                    continue
                for client in settings_raw.get("clients", []):
                    if client.get("email") == email:
                        return True
            return False
        return None
