from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_admin_pass, get_admin_user, load_env
from app.routes import subscriptions, users

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

security = HTTPBasic()


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    username = get_admin_user()
    password = get_admin_pass()
    valid_user = secrets.compare_digest(credentials.username, username)
    valid_pass = secrets.compare_digest(credentials.password, password)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def create_app() -> FastAPI:
    load_env()
    app = FastAPI(title="VPN Admin")

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
    app.include_router(users.router, dependencies=[Depends(require_auth)])
    app.include_router(subscriptions.router, dependencies=[Depends(require_auth)])

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        return RedirectResponse("/admin/users", status_code=status.HTTP_302_FOUND)

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_root(request: Request):
        return RedirectResponse("/admin/users", status_code=status.HTTP_302_FOUND)

    @app.get("/admin/health", response_class=HTMLResponse)
    async def health(request: Request):
        return templates.TemplateResponse(
            "health.html",
            {"request": request},
        )

    return app


app = create_app()
