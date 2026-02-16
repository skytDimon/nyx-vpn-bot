from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _public_base() -> str:
    return os.getenv(
        "SUB_PUBLIC_BASE",
        os.getenv("NL_SUB_PUBLIC_BASE", "https://nyxvpnnl.home.kg/sub"),
    )


app = FastAPI(title="VPN Subscription")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/health", response_class=HTMLResponse)
async def health(request: Request):
    return HTMLResponse("ok")


@app.get("/{sub_id}", response_class=HTMLResponse)
async def landing(request: Request, sub_id: str):
    sub_url = f"{_public_base().rstrip('/')}/{sub_id}"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sub_id": sub_id,
            "sub_url": sub_url,
        },
    )
