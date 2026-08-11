import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse
from neo4j import AsyncDriver

from app.core.config import settings
from app.core.database import get_driver
from app.core.security import create_session_token, get_current_user, get_optional_user
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
OAUTH_STATE_COOKIE = "oauth_state"


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
        "redirect_uri": f"{settings.BACKEND_URL}/auth/callback",
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
    )
    return response


@router.get("/callback")
async def callback(
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
    if not code or not state or not oauth_state or state != oauth_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{settings.BACKEND_URL}/auth/callback",
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

    session_token = create_session_token(user)
    response = RedirectResponse(url=settings.FRONTEND_URL)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        secure=False,
        path="/",
    )
    return response


@router.get("/session")
async def session(user=Depends(get_optional_user)):
    if not user:
        return {"user": None}
    return {
        "user": {
            "user_id": user["user_id"],
            "email": user.get("email"),
            "name": user.get("name"),
            "image": user.get("image"),
        }
    }


@router.post("/logout")
async def logout():
    from fastapi.responses import JSONResponse

    json_response = JSONResponse({"ok": True})
    json_response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
    )
    return json_response


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
