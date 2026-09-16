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

        # 3x-ui clients/add добавляет клиента в ОДИН инбаунд за вызов (поле
        # inboundUuid — единственное число). Поэтому проходим по каждому
        # настроенному id, резолвим его UUID и создаём клиента отдельно.
        uuid_by_id = {
            ib.get("id"): ib.get("uuid")
            for ib in await self._list_inbounds()
            if ib.get("id") in self._config.inbound_ids
        }

        errors: list[str] = []
        for inbound_id in self._config.inbound_ids:
            uuid = uuid_by_id.get(inbound_id)
            if not uuid:
                errors.append(f"inbound {inbound_id}: uuid not found on panel")
                continue
            ok, msg = await self._add_client_one_inbound(client, uuid, inbound_id)
            if not ok:
                errors.append(f"inbound {inbound_id}: {msg}")

        if errors:
            raise RuntimeError("XUI add_client failed: " + "; ".join(errors))
        return sub_id

    async def _add_client_one_inbound(self, client: dict, uuid: str, inbound_id: int) -> tuple[bool, str]:
        """Добавить клиента в один инбаунд. Пробует modern clients/add, затем legacy addClient."""
        last_msg = "no working endpoint"

        # 1. Modern 3x-ui API: /panel/api/clients/add, inboundUuid (один инбаунд).
        path = f"{self._config.base_path}/panel/api/clients/add"
        response = await self._post(path, {"client": client, "inboundUuid": uuid}, mode="json")
        ok, msg = self._ok(response)
        if ok:
            logger.info("XUI client added to inbound %s via clients/add", inbound_id)
            return True, msg
        last_msg = msg

        # 2/3. Legacy per-inbound API (числовой id, затем uuid).
        settings = {"clients": [client]}
        for payload_id, label in ((inbound_id, "id"), (uuid, "uuid")):
            payload = {"id": payload_id, "settings": json.dumps(settings)}
            for sub_path in (
                "/panel/api/inbounds/addClient",
                "/panel/inbound/addClient",
            ):
                path = f"{self._config.base_path}{sub_path}"
                for mode in ("data", "json"):
                    response = await self._post(path, payload, mode=mode)
                    ok, msg = self._ok(response)
                    if ok:
                        logger.info(
                            "XUI client added to inbound %s via %s (%s)",
                            inbound_id, sub_path, mode,
                        )
                        return True, msg
                    last_msg = msg
        return False, last_msg

    @staticmethod
    def _ok(response: httpx.Response) -> tuple[bool, str]:
        content_type = response.headers.get("content-type", "")
        if response.status_code == 404 or "application/json" not in content_type:
            return False, f"404/HTML on {response.request.url.path}"
        try:
            data = response.json()
        except json.JSONDecodeError:
            return False, f"non-JSON {response.status_code}"
        if data.get("success"):
            return True, "ok"
        return False, data.get("msg") or "rejected"

    async def _list_inbounds(self) -> list[dict]:
        """Сырые объекты инбаундов с панели (login вызывает вызывающий код)."""
        paths = [
            f"{self._config.base_path}/panel/api/inbounds/list",
            f"{self._config.base_path}/panel/api/inbound/list",
            f"{self._config.base_path}/panel/inbounds/list",
            f"{self._config.base_path}/panel/inbound/list",
            f"{self._config.base_path}/api/inbounds/list",
        ]
        for path in paths:
            response = await self._client.get(path)
            content_type = response.headers.get("content-type", "")
            if response.status_code == 404 or "application/json" not in content_type:
                continue
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                continue
            obj = data.get("obj") or data.get("data") or []
            if isinstance(obj, dict):
                obj = obj.get("list") or obj.get("items") or []
            return obj if isinstance(obj, list) else []
        raise RuntimeError("XUI inbounds list endpoint not found (_list_inbounds)")

    async def extend_client(
        self, email: str, days: int, current_end_at: datetime | None = None
    ) -> datetime:
        """Продлить клиента на `days` дней.

        Если `current_end_at` передан — новая дата = max(now, current_end_at) + days.
        Иначе читаем expiryTime из панели.
        """
        await self.login()
        base = current_end_at or await self._read_client_expiry(email)
        now = datetime.now(timezone.utc)
        anchor = base if (base and base > now) else now
        new_end_at = anchor + timedelta(days=days)
        expiry_time = int(new_end_at.timestamp() * 1000)

        ok = await self._update_client_expiry(email, expiry_time)
        if not ok:
            raise RuntimeError(f"XUI extend_client: failed to update expiry for {email}")
        logger.info("XUI client %s extended to %s", email, new_end_at)
        return new_end_at

    async def _read_client_expiry(self, email: str) -> datetime | None:
        result = await self.get_client_subscription(email)
        if not result:
            return None
        return result[1]

    async def _update_client_expiry(self, email: str, expiry_time_ms: int) -> bool:
        """Пробует modern update endpoint (v3.7.0), затем несколько путей.

        Панель ищет запись по uuid/email внутри полного объекта клиента,
        поэтому сначала читаем существующий объект через inbounds/list
        и отправляем его целиком с обновлённым expiryTime.
        """
        existing = await self._get_client_object(email)
        if existing is None:
            logger.warning("XUI client %s not found on panel, cannot update", email)
            return False
        updated = dict(existing)
        updated["expiryTime"] = expiry_time_ms
        updated["enable"] = True
        paths = [
            f"{self._config.base_path}/panel/api/clients/update/{email}",
            f"{self._config.base_path}/panel/api/clients/update",
        ]
        for path in paths:
            for payload in (
                {"client": updated},
                updated,
                {"email": email, "expiryTime": expiry_time_ms},
            ):
                response = await self._post(path, payload, mode="json")
                content_type = response.headers.get("content-type", "")
                if response.status_code == 404 or "application/json" not in content_type:
                    continue
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    continue
                if data.get("success"):
                    logger.info("XUI expiry updated via %s", path)
                    return True
                logger.warning("XUI update via %s rejected: %s", path, data.get("msg"))
        return False

    async def list_all_clients(self) -> list[dict]:
        """Все клиенты на настроенных inbound'ах. Логин вызывает вызывающий код."""
        paths = [
            f"{self._config.base_path}/panel/api/inbounds/list",
            f"{self._config.base_path}/panel/api/inbound/list",
            f"{self._config.base_path}/panel/inbounds/list",
            f"{self._config.base_path}/panel/inbound/list",
            f"{self._config.base_path}/api/inbounds/list",
        ]
        for path in paths:
            response = await self._client.get(path)
            content_type = response.headers.get("content-type", "")
            if response.status_code == 404 or "application/json" not in content_type:
                continue
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                continue
            obj = data.get("obj") or data.get("data") or []
            if isinstance(obj, dict):
                obj = obj.get("list") or obj.get("items") or []
            out: list[dict] = []
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
                for client in settings.get("clients", []):
                    email = client.get("email")
                    sub_id = client.get("subId") or client.get("sub_id") or ""
                    expiry = client.get("expiryTime") or 0
                    if not email:
                        continue
                    out.append({
                        "email": email,
                        "subId": sub_id,
                        "expiryTime": int(expiry) if expiry else 0,
                        "enable": bool(client.get("enable")),
                        "inbound_id": inbound.get("id"),
                    })
            return out
        raise RuntimeError("XUI inbounds list endpoint not found (list_all_clients)")

    async def _get_client_object(self, email: str) -> dict | None:
        """Вернуть сырой объект клиента из inbounds/list по email."""
        paths = [
            f"{self._config.base_path}/panel/api/inbounds/list",
            f"{self._config.base_path}/panel/api/inbound/list",
            f"{self._config.base_path}/panel/inbounds/list",
            f"{self._config.base_path}/panel/inbound/list",
            f"{self._config.base_path}/api/inbounds/list",
        ]
        for path in paths:
            response = await self._client.get(path)
            content_type = response.headers.get("content-type", "")
            if response.status_code == 404 or "application/json" not in content_type:
                continue
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                continue
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
                for client in settings.get("clients", []):
                    if client.get("email") == email:
                        return client
        return None

    async def get_client_traffic(self, email: str) -> dict | None:
        await self.login()
        paths = [
            f"{self._config.base_path}/panel/api/clients/{email}/traffic",
            f"{self._config.base_path}/panel/api/client/{email}/traffic",
        ]
        for path in paths:
            response = await self._client.get(path)
            content_type = response.headers.get("content-type", "")
            if response.status_code == 404 or "application/json" not in content_type:
                continue
            response.raise_for_status()
            data = response.json()
            obj = data.get("obj") or data.get("data") or {}
            if isinstance(obj, dict):
                return {
                    "up": int(obj.get("up", 0) or 0),
                    "down": int(obj.get("down", 0) or 0),
                    "total": int(obj.get("total") or obj.get("traffic") or 0),
                }
        return None

    async def delete_client(self, email: str) -> bool:
        await self.login()
        paths = [
            f"{self._config.base_path}/panel/api/clients/delete/{email}",
        ]
        for path in paths:
            response = await self._post(path, {}, mode="json")
            content_type = response.headers.get("content-type", "")
            if response.status_code == 404 or "application/json" not in content_type:
                continue
            try:
                data = response.json()
            except json.JSONDecodeError:
                continue
            if data.get("success"):
                logger.info("XUI client %s deleted", email)
                return True
        return False

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
