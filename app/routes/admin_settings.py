from __future__ import annotations

import hmac
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.auth.sessions import require_admin
from app.db.repositories import read_app_settings, write_app_settings
from app.stats.collector import log_event

router = APIRouter()


@router.get("/admin/settings", response_class=HTMLResponse)
async def get_settings(request: Request, _admin=Depends(require_admin)):
    values = await read_app_settings()
    lang = values.get("default_lang", "ru")
    interval = values.get("banner_rotation_interval", "30")
    announcement = escape(values.get("announcement_text", ""), quote=True)
    maintenance = values.get("maintenance_mode", "false") == "true"
    return HTMLResponse(
        f"<h1>Настройки</h1><form method='post'><input type='hidden' name='csrf_token' value='{escape(request.cookies.get('vb_csrf', ''), quote=True)}'><label>Язык <select name='default_lang'><option value='ru' {'selected' if lang == 'ru' else ''}>Русский</option><option value='en' {'selected' if lang == 'en' else ''}>English</option></select></label><p><label>Интервал баннеров, сек <input type='number' min='10' max='600' name='banner_rotation_interval' value='{interval}'></label></p><p><label>Объявление <input name='announcement_text' maxlength='240' value='{announcement}'></label></p><p><label><input type='checkbox' name='maintenance_mode' value='true' {'checked' if maintenance else ''}> Режим обслуживания</label></p><button>Сохранить</button></form><p><a href='/admin/'>Назад</a></p>"
    )


@router.post("/admin/settings", response_class=HTMLResponse)
async def post_settings(
    request: Request,
    csrf_token: str = Form(...),
    default_lang: str = Form(...),
    banner_rotation_interval: int = Form(...),
    announcement_text: str = Form(""),
    maintenance_mode: bool = Form(False),
    _admin=Depends(require_admin),
):
    cookie_token = request.cookies.get("vb_csrf", "")
    if not cookie_token or not hmac.compare_digest(cookie_token, csrf_token):
        raise HTTPException(403, "CSRF token mismatch")
    if default_lang not in {"ru", "en"} or not 10 <= banner_rotation_interval <= 600:
        raise HTTPException(400, "Invalid settings")
    await write_app_settings(
        {
            "default_lang": default_lang,
            "banner_rotation_interval": str(banner_rotation_interval),
            "announcement_text": announcement_text[:240],
            "maintenance_mode": "true" if maintenance_mode else "false",
        }
    )
    try:
        await log_event("admin_action", status="ok", meta_json="settings_update")
    except Exception:
        pass
    return HTMLResponse("Сохранено. <a href='/admin/settings'>Назад</a>")


@router.get("/public-settings")
async def public_settings():
    values = await read_app_settings()
    return {
        "default_lang": values.get("default_lang", "ru"),
        "banner_rotation_interval": int(values.get("banner_rotation_interval", "30")),
        "announcement_text": values.get("announcement_text", ""),
        "maintenance_mode": values.get("maintenance_mode", "false") == "true",
    }
