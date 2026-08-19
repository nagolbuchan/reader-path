import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from neo4j import AsyncDriver

from app.core.config import settings
from app.core.database import get_driver
from app.core.security import (
    create_session_token,
    decode_session_token,
    get_current_user,
    get_optional_user,
)
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
OAUTH_STATE_COOKIE = "oauth_state"


def _oauth_redirect_uri() -> str:
    return f"{settings.oauth_redirect_base}/auth/callback"


def _set_session_cookie(response: RedirectResponse | JSONResponse, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        secure=False,
        path="/",
    )


@router.get("/login")
async def login():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": _oauth_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "include_granted_scopes": "true",
        "state": state,
        "prompt": "select_account",
    }
    response = RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        samesite="lax",
        max_age=600,
        secure=False,
        path="/",
    )
    return response


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    oauth_state: Optional[str] = Cookie(default=None, alias=OAUTH_STATE_COOKIE),
    driver: AsyncDriver = Depends(get_driver),
):
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?auth_error={error}"
        )

    # Prefer Cookie() dependency, fall back to raw request cookies (proxy-safe)
    state_cookie = oauth_state or request.cookies.get(OAUTH_STATE_COOKIE)
    if not code or not state or not state_cookie or state != state_cookie:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": _oauth_redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange OAuth code: {token_resp.text}",
            )
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token from Google")

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")
        info = userinfo_resp.json()

    google_sub = info.get("sub")
    if not google_sub:
        raise HTTPException(status_code=400, detail="Google user missing sub")

    user_repo = UserRepository(driver)
    user = await user_repo.merge_user(
        user_id=f"google_{google_sub}",
        email=info.get("email"),
        name=info.get("name") or info.get("email") or "Reader",
        image=info.get("picture"),
        provider="google",
    )
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user")

    try:
        session_token = create_session_token(user)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = RedirectResponse(url=settings.FRONTEND_URL)
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    _set_session_cookie(response, session_token)
    return response


@router.get("/session")
async def session(request: Request, user=Depends(get_optional_user)):
    if user:
        return {
            "user": {
                "user_id": user["user_id"],
                "email": user.get("email"),
                "name": user.get("name"),
                "image": user.get("image"),
            }
        }

    # Debug aids while tracking cookie/JWT issues (safe: no token contents)
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    debug = {
        "cookie_present": bool(token),
        "cookie_name": settings.SESSION_COOKIE_NAME,
        "cookies_seen": list(request.cookies.keys()),
    }
    if token:
        try:
            payload = decode_session_token(token)
            debug["jwt_sub"] = payload.get("sub")
            debug["jwt_ok"] = True
        except HTTPException as exc:
            debug["jwt_ok"] = False
            debug["jwt_error"] = exc.detail

    if settings.DEBUG:
        return {"user": None, "debug": debug}
    return {"user": None}


@router.post("/logout")
async def logout():
    json_response = JSONResponse({"ok": True})
    json_response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
    )
    return json_response


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
