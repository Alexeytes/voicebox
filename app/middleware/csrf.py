import hmac
from urllib.parse import urlsplit

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith(
            "/admin/"
        ):
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            expected_scheme = (
                request.headers.get("x-forwarded-proto", request.url.scheme)
                if settings.TRUST_PROXY
                else request.url.scheme
            )
            expected = expected_scheme + "://" + request.headers.get("host", request.url.netloc)
            observed = origin or (
                referer and (urlsplit(referer).scheme + "://" + urlsplit(referer).netloc)
            )
            if not observed or observed.rstrip("/") != expected.rstrip("/"):
                return JSONResponse({"detail": "Origin check failed"}, status_code=403)
            # Form routes validate their hidden token in the handler. Fetch mutations must send the header.
            if request.url.path not in {"/admin/login", "/admin/logout", "/admin/settings"}:
                header_token = request.headers.get("x-csrf-token", "")
                cookie_token = request.cookies.get("vb_csrf", "")
                if not cookie_token or not hmac.compare_digest(cookie_token, header_token):
                    return JSONResponse({"detail": "CSRF token mismatch"}, status_code=403)
        return await call_next(request)
