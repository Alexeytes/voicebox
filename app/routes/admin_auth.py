from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth.passwords import verify_password
from app.auth.sessions import SESSION_COOKIE, create_session, require_admin
from app.config import settings
from app.db.repositories import get_user_by_username
from app.stats.collector import log_event

router = APIRouter()
_attempts: dict[str, deque[float]] = defaultdict(deque)


@router.get("/admin/login", response_class=HTMLResponse)
def login_form():
    csrf = secrets.token_urlsafe(32)
    response = HTMLResponse(
        """<!doctype html><html lang='ru'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Вход · Voice Box</title><body style='font:16px system-ui;background:#101720;color:#eef;padding:8vh 7vw'><main style='max-width:420px;margin:auto'><a href='/' style='color:#9be5c1'>← Voice Box</a><h1>Панель управления</h1><form method='post' style='display:grid;gap:14px'><input type='hidden' name='csrf_token' value='TOKEN_PLACEHOLDER'><label>Логин<input name='username' autocomplete='username' required style='display:block;width:100%;padding:12px;margin-top:5px'></label><label>Пароль<input name='password' type='password' autocomplete='current-password' required style='display:block;width:100%;padding:12px;margin-top:5px'></label><button style='padding:12px;background:#9be5c1;border:0;border-radius:8px;font-weight:bold'>Войти</button></form></main></body></html>""".replace(
            "TOKEN_PLACEHOLDER", csrf
        )
    )
    response.set_cookie(
        "vb_csrf", csrf, httponly=False, secure=settings.HTTPS_ONLY, samesite="lax", path="/admin"
    )
    return response


@router.post("/admin/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
):
    cookie_token = request.cookies.get("vb_csrf", "")
    if not cookie_token or not hmac.compare_digest(cookie_token, csrf_token):
        raise HTTPException(403, "CSRF token mismatch")
    client_ip = request.client.host if request.client else "unknown"
    client_ip_hash = hashlib.sha256((client_ip + settings.IP_HASH_SALT).encode()).hexdigest()
    key = client_ip
    now = time.monotonic()
    attempts = _attempts[key]
    while attempts and now - attempts[0] > settings.ADMIN_ATTEMPT_WINDOW_MIN * 60:
        attempts.popleft()
    if len(attempts) >= settings.ADMIN_LOGIN_ATTEMPTS:
        raise HTTPException(429, "Слишком много попыток входа")
    attempts.append(now)
    if len(_attempts) > 10000:
        for stale_key in [
            k
            for k, bucket in _attempts.items()
            if not bucket or now - bucket[-1] > settings.ADMIN_ATTEMPT_WINDOW_MIN * 60
        ]:
            _attempts.pop(stale_key, None)
    user = await get_user_by_username(username)
    if not user or not await asyncio.to_thread(verify_password, password, user.password_hash):
        try:
            await log_event("login_failed", status="error", ip_hash=client_ip_hash)
        except Exception:
            pass
        raise HTTPException(401, "Неверный логин или пароль")
    attempts.clear()
    response = RedirectResponse("/admin/", status_code=303)
    csrf = secrets.token_urlsafe(32)
    response.set_cookie(
        SESSION_COOKIE,
        create_session(user.id),
        httponly=True,
        secure=settings.HTTPS_ONLY,
        samesite="lax",
        path="/admin",
        max_age=settings.ADMIN_SESSION_TTL,
    )
    response.set_cookie(
        "vb_csrf",
        csrf,
        httponly=False,
        secure=settings.HTTPS_ONLY,
        samesite="lax",
        path="/admin",
        max_age=settings.ADMIN_SESSION_TTL,
    )
    try:
        await log_event("login_success", status="ok", ip_hash=client_ip_hash)
    except Exception:
        pass
    return response


@router.post("/admin/logout")
def logout(request: Request, csrf_token: str = Form(...), _admin=Depends(require_admin)):
    cookie_token = request.cookies.get("vb_csrf", "") if request else ""
    if not cookie_token or not hmac.compare_digest(cookie_token, csrf_token):
        raise HTTPException(403, "CSRF token mismatch")
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/admin")
    response.delete_cookie("vb_csrf", path="/admin")
    return response


@router.get("/admin/", response_class=HTMLResponse)
def admin_page(request: Request, _admin=Depends(require_admin)):
    csrf = request.cookies.get("vb_csrf", "")
    html = """<!doctype html><html lang='ru'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Панель · Voice Box</title><body style='font:15px system-ui;background:#101720;color:#eef;padding:28px;max-width:1000px;margin:auto'><header style='display:flex;justify-content:space-between'><a href='/' style='color:#9be5c1'>← Voice Box</a><form method='post' action='/admin/logout'><input type='hidden' name='csrf_token' value='TOKEN_PLACEHOLDER'><button>Выйти</button></form></header><h1>Панель управления</h1><h2>Статистика</h2><p><a href='/admin/stats' style='color:#9be5c1'>Открыть отчёт, график и журнал событий</a></p><pre id='stats'>Загрузка…</pre><h2>Рекламные баннеры</h2><p><a href='/admin/settings' style='color:#9be5c1'>Настройки сайта</a></p><p>Размещения top, between, sidebar, bottom ведут на рекламные места главной страницы.</p><form id='banner-form' style='display:grid;gap:10px;max-width:560px'><input name='title' placeholder='Название' required><input name='target_url' type='url' placeholder='https:// рекламодатель' required><input name='image' type='file' accept='image/png,image/jpeg,image/gif,image/webp' required><input name='alt_text' placeholder='Описание изображения'><input name='weight' type='number' min='0' value='1'><label>Начало показа <input name='active_from' type='datetime-local'></label><label>Конец показа <input name='active_to' type='datetime-local'></label><label><input name='enabled' type='checkbox' checked> Активен</label><textarea name='html_snippet' placeholder='Необязательно: разрешённый HTML баннера'></textarea><select name='position'><option>top</option><option>between</option><option>sidebar</option><option>bottom</option></select><button>Добавить баннер</button></form><p id='message'></p><ul id='banners'></ul><script src='/static/admin.js' defer></script></body></html>""".replace(
        "TOKEN_PLACEHOLDER", escape(csrf)
    )
    return HTMLResponse(html)
