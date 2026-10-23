import time

from fastapi import HTTPException, Request
from itsdangerous import URLSafeTimedSerializer

from app.config import settings
from app.db.repositories import get_user_by_id

SESSION_COOKIE = "vb_session"
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def create_session(user_id: int) -> str:
    return serializer.dumps({"uid": user_id, "iat": int(time.time())})


def decode_session(token: str, max_age: int = settings.ADMIN_SESSION_TTL):
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except Exception:
        return None



async def require_admin(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    session = decode_session(token) if token else None
    user = await get_user_by_id(session.get("uid")) if session else None
    if not user:
        raise HTTPException(status_code=401, detail="Войдите в панель администратора")
    return user
