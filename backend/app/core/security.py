from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Cookie, HTTPException, status

from app.core.config import settings


def create_session_token(user: Dict[str, Any]) -> str:
    user_id = user.get("user_id") or user.get("userId")
    if not user_id:
        raise ValueError("Cannot create session token without user_id")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": user.get("email"),
        "name": user.get("name"),
        "image": user.get("image"),
        "iat": now,
        "exp": now + timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS),
    }
    return jwt.encode(payload, settings.AUTH_SECRET, algorithm="HS256")


def decode_session_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.AUTH_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        ) from exc


def _user_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session payload",
        )
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "name": payload.get("name"),
        "image": payload.get("image"),
    }


async def get_current_user(
    readerpath_session: Optional[str] = Cookie(
        default=None, alias=settings.SESSION_COOKIE_NAME
    ),
) -> Dict[str, Any]:
    if not readerpath_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_session_token(readerpath_session)
    return _user_from_payload(payload)


async def get_optional_user(
    readerpath_session: Optional[str] = Cookie(
        default=None, alias=settings.SESSION_COOKIE_NAME
    ),
) -> Optional[Dict[str, Any]]:
    if not readerpath_session:
        return None
    try:
        payload = decode_session_token(readerpath_session)
        return _user_from_payload(payload)
    except HTTPException:
        return None
