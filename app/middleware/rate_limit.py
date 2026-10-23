import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

# Rate limit buckets
BUCKETS = defaultdict(lambda: deque())
BUCKETS_PREVIEW = defaultdict(lambda: deque())
BUCKETS_ADMIN_READ = defaultdict(lambda: deque())
BUCKETS_ADMIN_WRITE = defaultdict(lambda: deque())
BUCKET_LOCK = threading.Lock()

# Configurable parameters
RATE_LIMIT_REQUESTS = getattr(settings, "RATE_LIMIT_REQUESTS", 5)
RATE_LIMIT_INTERVAL_SEC = getattr(settings, "RATE_LIMIT_INTERVAL_SEC", 60)
PREVIEW_RATE_LIMIT = getattr(settings, "PREVIEW_RATE_LIMIT", 3)
PREVIEW_INTERVAL_SEC = getattr(settings, "PREVIEW_INTERVAL_SEC", 60)


def get_client_ip(request: Request) -> str:
    if getattr(settings, "TRUST_PROXY", False):
        ip = request.headers.get("x-forwarded-for", request.client.host)
        # x-forwarded-for может содержать список, берём первый
        return ip.split(",")[0].strip() if ip else request.client.host
    return request.client.host


def check_and_add_request(ip: str, bucket: dict, limit: int, interval: int) -> bool:
    now = time.monotonic()
    with BUCKET_LOCK:
        events = bucket[ip]
        while events and now - events[0] > interval:
            events.popleft()
        if len(events) >= limit:
            return False
        events.append(now)
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        ip = get_client_ip(request)
        # Административные чтения и изменения имеют отдельные лимиты.
        if path.startswith("/admin/") and path != "/admin/login":
            if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                allowed = check_and_add_request(ip, BUCKETS_ADMIN_WRITE, 10, 60)
            else:
                allowed = check_and_add_request(ip, BUCKETS_ADMIN_READ, 30, 60)
        # Превью — отдельный бакет
        elif path.startswith("/voices/preview"):
            allowed = check_and_add_request(
                ip, BUCKETS_PREVIEW, PREVIEW_RATE_LIMIT, PREVIEW_INTERVAL_SEC
            )
        elif path.startswith("/synthesize"):
            allowed = check_and_add_request(
                ip, BUCKETS, RATE_LIMIT_REQUESTS, RATE_LIMIT_INTERVAL_SEC
            )
        else:
            return await call_next(request)
        if not allowed:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        return await call_next(request)


def reset_rate_limit_state():
    with BUCKET_LOCK:
        BUCKETS.clear()
        BUCKETS_PREVIEW.clear()
        BUCKETS_ADMIN_READ.clear()
        BUCKETS_ADMIN_WRITE.clear()
