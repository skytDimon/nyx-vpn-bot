from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import jwt
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import get_bot_username
from app.db import get_subscription, get_user

BASE_DIR = Path(__file__).resolve().parents[2]
router = APIRouter(prefix="/cabinet", tags=["cabinet"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


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
    """API для получения данных подписки."""
    tg_id = _decode_token(t)

    user = get_user(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sub = get_subscription(tg_id)

    now = datetime.now(timezone.utc)
    is_active = False
    days_left = None

    if sub and sub.get("end_at"):
        end_at = sub["end_at"]
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=timezone.utc)
        is_active = end_at > now
        if is_active:
            days_left = (end_at - now).days

    response = {
        "username": user.get("username") or f"tg_{tg_id}",
        "tg_id": tg_id,
        "is_active": is_active,
        "subscription": None,
        "referral_balance": int(user.get("referral_balance") or 0),
    }

    if sub:
        response["subscription"] = {
            "start_at": sub["start_at"].isoformat() if sub.get("start_at") else None,
            "end_at": sub["end_at"].isoformat() if sub.get("end_at") else None,
            "days_left": days_left,
            "subscription_link": sub.get("subscription_link"),
            "instructions": sub.get("instructions"),
        }

    return JSONResponse(response)
