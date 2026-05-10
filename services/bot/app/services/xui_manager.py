from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.config import get_api_base_url, get_api_key

logger = logging.getLogger(__name__)


@dataclass
class AddClientResult:
    success: bool
    username: str
    client_uuid: str
    sub_id: str
    subscription_url: str
    servers: list[dict]
    message: str


class XuiManagerClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key or get_api_key()
        self._base_url = (base_url or get_api_base_url()).rstrip("/")
        self._client = httpx.AsyncClient(timeout=15.0)

    async def add_client(self, username: str, days: int = 3) -> AddClientResult:
        url = f"{self._base_url}/api/add_client"
        headers = {"X-API-Key": self._api_key}
        payload = {"username": username, "days": days}
        resp = await self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return AddClientResult(
            success=data.get("success", False),
            username=data.get("username", ""),
            client_uuid=data.get("client_uuid", ""),
            sub_id=data.get("sub_id", ""),
            subscription_url=data.get("subscription_url", ""),
            servers=data.get("servers", []),
            message=data.get("message", ""),
        )

    async def close(self) -> None:
        await self._client.aclose()

