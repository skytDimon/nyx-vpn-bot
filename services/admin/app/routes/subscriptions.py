from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import fetch_subscriptions, get_subscription, update_subscription

BASE_DIR = Path(__file__).resolve().parents[2]
router = APIRouter(prefix="/admin", tags=["subscriptions"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _page_limit(value: int | None) -> int:
    if not value or value <= 0:
        return 50
    return min(value, 200)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid datetime format") from exc


@router.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_list(request: Request, page: int = 1, limit: int = 50):
    limit = _page_limit(limit)
    page = max(page, 1)
    offset = (page - 1) * limit
    result = fetch_subscriptions(limit, offset)
    total_pages = max((result.total + limit - 1) // limit, 1)

    return templates.TemplateResponse(
        "subscriptions.html",
        {
            "request": request,
            "subscriptions": result.items,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
    )


@router.get("/subscriptions/{tg_id}", response_class=HTMLResponse)
async def subscription_detail(request: Request, tg_id: int):
    subscription = get_subscription(tg_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return templates.TemplateResponse(
        "subscription_detail.html",
        {"request": request, "subscription": subscription},
    )


@router.post("/subscriptions/{tg_id}")
async def subscription_update(
    tg_id: int,
    start_at: str | None = Form(default=None),
    end_at: str | None = Form(default=None),
    subscription_link: str | None = Form(default=None),
    instructions: str | None = Form(default=None),
):
    update_subscription(
        tg_id,
        _parse_dt(start_at),
        _parse_dt(end_at),
        subscription_link or None,
        instructions or None,
    )
    return RedirectResponse(f"/admin/subscriptions/{tg_id}", status_code=303)
