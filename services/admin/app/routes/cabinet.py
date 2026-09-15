from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import jwt
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import get_bot_username, get_xui_settings
from app.db import get_subscription, get_user
from app.services.xui_panel import XuiCabinetChecker

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
router = APIRouter(prefix="/cabinet", tags=["cabinet"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Кэш живой сверки с панелью: tg_id → (is_present|None, expires_monotonic).
# Панель не дёргается на каждую загрузку страницы; None (панель недоступна) НЕ кэшируем.
_PANEL_CACHE_TTL = 60.0
_panel_cache: dict[int, tuple[bool, float]] = {}
_panel_lock = asyncio.Lock()


async def _panel_client_present(email: str | None, tg_id: int) -> bool | None:
    """True — клиент на панели; False — точно удалён; None — проверить нельзя."""
    if not email:
        return None
    if get_xui_settings() is None:
        return None
    now = time.monotonic()
    cached = _panel_cache.get(tg_id)
    if cached and cached[1] > now:
        return cached[0]
    async with _panel_lock:
        cached = _panel_cache.get(tg_id)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        checker = XuiCabinetChecker(get_xui_settings())
        try:
            present = await checker.client_exists(email)
        except Exception:
            logger.warning("cabinet panel check failed for %s", email, exc_info=True)
            present = None
        finally:
            await checker.close()
        if present is not None:
            _panel_cache[tg_id] = (present, time.monotonic() + _PANEL_CACHE_TTL)
        return present


def _decode_token(token: str) -> int:
    """Декодировать JWT и вернуть tg_id. Raises HTTPException если невалидный."""
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        tg_id = int(payload.get("sub", 0))
        if tg_id <= 0:
            raise ValueError("Invalid tg_id")
        return tg_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("", response_class=HTMLResponse)
async def cabinet_page(request: Request, t: str = Query(...)):
    """HTML-страница личного кабинета."""
    tg_id = _decode_token(t)
    return templates.TemplateResponse(
        "cabinet.html",
        {"request": request, "token": t, "tg_id": tg_id, "bot_username": get_bot_username()},
    )


@router.get("/api/subscription")
async def cabinet_api(t: str = Query(...)):
    """API для получения данных подписки. Сверяет client_uuid с панелью."""
    tg_id = _decode_token(t)

    user = get_user(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sub = get_subscription(tg_id)

    now = datetime.now(timezone.utc)
    is_active = False
    days_left = None
    reason: str | None = None

    if sub and sub.get("end_at"):
        end_at = sub["end_at"]
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=timezone.utc)
        is_active = end_at > now
        if is_active:
            days_left = (end_at - now).days

    # Живая сверка с панелью — переносили туда же, где ранее стоял cabinet_sync.
    panel_removed = False
    if is_active and sub and sub.get("client_uuid"):
        present = await _panel_client_present(sub.get("client_uuid"), tg_id)
        if present is False:
            # Клиент удалён на панели — в кабинете показываем неактивной + причину.
            is_active = False
            days_left = None
            panel_removed = True
            reason = "deleted_from_panel"

    response = {
        "username": user.get("username") or f"tg_{tg_id}",
        "tg_id": tg_id,
        "is_active": is_active,
        "reason": reason,
        "subscription": None,
        "referral_balance": int(user.get("referral_balance") or 0),
    }

    if sub:
        # Панель-ссылка не отдаётся как действующая, если клиент удалён.
        link = None if panel_removed else sub.get("subscription_link")
        response["subscription"] = {
            "start_at": sub["start_at"].isoformat() if sub.get("start_at") else None,
            "end_at": sub["end_at"].isoformat() if sub.get("end_at") else None,
            "days_left": days_left,
            "subscription_link": link,
            "instructions": sub.get("instructions"),
        }

    return JSONResponse(response)
