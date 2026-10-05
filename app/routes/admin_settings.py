from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

from app.config import settings

router = APIRouter()

@router.get("/admin/settings", response_class=HTMLResponse)
def get_settings():
    html = f"""
    <form method='post'>
      <label>Default lang: <input name='default_lang' value='{getattr(settings, 'DEFAULT_LANG', 'ru')}'></label><br>
      <label>Rotation interval: <input type='number' name='banner_rotation_interval' value='{getattr(settings, 'BANNER_ROTATION_INTERVAL', 30)}'></label><br>
      <label>Maintenance mode: <input type='checkbox' name='maintenance_mode' {'checked' if getattr(settings, 'MAINTENANCE_MODE', False) else ''}></label><br>
      <label>Announcement: <input name='announcement_text' value='{getattr(settings, 'ANNOUNCEMENT_TEXT', '')}'></label><br>
      <button>Сохранить</button>
    </form>"""
    return HTMLResponse(html)

@router.post("/admin/settings", response_class=HTMLResponse)
def post_settings(default_lang: str = Form(...), banner_rotation_interval: int = Form(...), maintenance_mode: bool = Form(False), announcement_text: str = Form("")):
    # Здесь только mock памяти, без записи в .env/config (для runtime demo)
    settings.DEFAULT_LANG = default_lang
    settings.BANNER_ROTATION_INTERVAL = banner_rotation_interval
    settings.MAINTENANCE_MODE = maintenance_mode
    settings.ANNOUNCEMENT_TEXT = announcement_text
    return HTMLResponse("Сохранено. <a href='/admin/settings'>Назад</a>")
