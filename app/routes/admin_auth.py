from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth.passwords import hash_password, verify_password
from app.auth.sessions import create_session, SESSION_COOKIE
from app.db.repositories import get_user_by_username
from app.config import settings

router = APIRouter()

@router.get("/admin/login", response_class=HTMLResponse)
def login_form(request: Request):
    return HTMLResponse("<form method='post'><input name='username'><input type='password' name='password'><button>Login</button></form>")

@router.post("/admin/login")
def login(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    import asyncio
    user = asyncio.run(get_user_by_username(username))
    if not user or not verify_password(password, user.password_hash):
        return HTMLResponse("Invalid credentials", status_code=401)
    session = create_session(user.id)
    resp = RedirectResponse("/admin/", status_code=302)
    resp.set_cookie(key=SESSION_COOKIE, value=session, httponly=True, samesite="lax")
    return resp
