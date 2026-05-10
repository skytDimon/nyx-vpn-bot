from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import delete_user, fetch_users, get_user, update_user

BASE_DIR = Path(__file__).resolve().parents[2]
router = APIRouter(prefix="/admin", tags=["users"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _page_limit(value: int | None) -> int:
    if not value or value <= 0:
        return 50
    return min(value, 200)


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request, search: str | None = None, page: int = 1, limit: int = 50
):
    limit = _page_limit(limit)
    page = max(page, 1)
    offset = (page - 1) * limit
    result = fetch_users(search, limit, offset)
    total_pages = max((result.total + limit - 1) // limit, 1)

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": result.items,
            "search": search or "",
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        },
    )


@router.get("/users/{tg_id}", response_class=HTMLResponse)
async def user_detail(request: Request, tg_id: int):
    user = get_user(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        "user_detail.html",
        {"request": request, "user": user},
    )


@router.post("/users/{tg_id}")
async def user_update(
    tg_id: int,
    username: str | None = Form(default=None),
    balance: int = Form(...),
    referral_balance: int = Form(...),
):
    update_user(tg_id, username or None, balance, referral_balance)
    return RedirectResponse(f"/admin/users/{tg_id}", status_code=303)


@router.post("/users/{tg_id}/delete")
async def user_delete(tg_id: int):
    delete_user(tg_id)
    return RedirectResponse("/admin/users", status_code=303)
