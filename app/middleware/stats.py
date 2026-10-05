from starlette.middleware.base import BaseHTTPMiddleware
from app.stats.collector import log_event
from app.config import settings
import hashlib, json, asyncio

class StatsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # фрагмент — писать события по ключевым роутам
        ip = request.client.host
        ip_hash = hashlib.sha256((ip + settings.IP_HASH_SALT).encode()).hexdigest()
        path = request.url.path
        response = await call_next(request)
        if path.startswith("/synthesize"):
            # пример
            asyncio.create_task(log_event("synthesis_requested", ip_hash=ip_hash, lang=request.query_params.get('lang')))
        return response
