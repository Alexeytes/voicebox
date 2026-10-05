import time

from itsdangerous import URLSafeTimedSerializer

from app.config import settings

SESSION_COOKIE = 'vb_session'
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def create_session(user_id: int) -> str:
    return serializer.dumps({'uid': user_id, 'iat': int(time.time())})

def decode_session(token: str, max_age: int = settings.ADMIN_SESSION_TTL):
    try:
        data = serializer.loads(token, max_age=max_age)
        return data
    except Exception:
        return None
