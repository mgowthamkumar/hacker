import time
import secrets
from typing import Optional
from fastapi import Request, Response, Depends, HTTPException, status
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def create_session_token(user_id: str) -> str:
    """Generates a cryptographically signed session token with timestamp."""
    data = {"uid": user_id, "nonce": secrets.token_hex(8), "t": time.time()}
    return serializer.dumps(data)


def verify_session_token(token: str, max_age_days: int = 30) -> Optional[str]:
    """Verifies signed token and returns user_id if valid."""
    try:
        data = serializer.loads(token, max_age=max_age_days * 86400)
        return data.get("uid")
    except (BadSignature, SignatureExpired):
        return None


def set_session_cookie(response: Response, user_id: str):
    """Sets an HttpOnly, secure-ready session cookie on the response."""
    token = create_session_token(user_id)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_DAYS * 86400,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True if strictly running under HTTPS
        path="/"
    )
    return token


def clear_session_cookie(response: Response):
    """Clears the session cookie."""
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/"
    )


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Retrieves authenticated user from cookie or Bearer header, or None if guest."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    user_id = verify_session_token(token, settings.SESSION_MAX_AGE_DAYS)
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def get_current_user(user: Optional[User] = Depends(get_current_user_optional)) -> User:
    """FastAPI dependency requiring active authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )
    return user
