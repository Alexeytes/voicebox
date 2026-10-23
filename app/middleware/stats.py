from __future__ import annotations

import asyncio
import hashlib
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.stats.collector import log_event

logger = logging.getLogger(__name__)


class StatsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ip = request.client.host if request.client else "unknown"
        ip_hash = hashlib.sha256((ip + settings.IP_HASH_SALT).encode()).hexdigest()
        path = request.url.path
        started = time.monotonic()
        response = await call_next(request)
        event = None
        if path == "/synthesize" and request.method == "POST":
            event = "synthesis_requested"
        elif path == "/voices/preview" and request.method == "POST":
            event = "preview_requested"
        if event:
            if response.status_code >= 400:
                event = "synthesis_error" if event == "synthesis_requested" else "preview_error"

            async def record():
                try:
                    await log_event(
                        event,
                        ip_hash=ip_hash,
                        status=str(response.status_code),
                        duration_ms=int((time.monotonic() - started) * 1000),
                    )
                except Exception:
                    logger.exception("Could not record stats event %s", event)

            asyncio.create_task(record())
        return response
