from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.repositories import read_app_settings


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith(("/admin", "/static", "/data/banners")):
            return await call_next(request)
        settings = await read_app_settings()
        if settings.get("maintenance_mode") == "true":
            return HTMLResponse(
                "<h1>Короткая пауза</h1><p>Voice Box проходит обслуживание. Попробуйте позже.</p>",
                status_code=503,
            )
        return await call_next(request)
