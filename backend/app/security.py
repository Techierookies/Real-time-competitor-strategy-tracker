"""
Authentication.

What was wrong before
---------------------
Passwords were stored as a bare `hashlib.sha256(password)` digest. SHA-256 is
designed to be fast, which is exactly the wrong property for a password hash:
commodity hardware tries billions of candidates per second, and because the
digest was unsalted, two users with the same password produced the same hash
and a single rainbow table would have broken every account at once.

There was also no session concept. The login endpoint took an `isAdmin` flag
from the request body, and the frontend kept the resulting user object in
localStorage. Nothing after login ever re-verified who the caller was, so any
client could call an admin endpoint directly.

This module uses bcrypt (deliberately slow, individually salted) and issues
signed JWTs that carry the role. Admin endpoints verify the token's role claim
server-side on every request.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import Settings, get_settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return password_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return password_context.verify(plain, hashed)
    except ValueError:
        # A stored hash in an unrecognised format (for example a legacy
        # SHA-256 digest from the previous schema) must fail closed.
        return False


def create_access_token(subject: str, role: str, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings) -> dict:
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = decode_token(credentials.credentials, settings)
    return {"email": claims.get("sub"), "role": claims.get("role", "user")}


def require_admin(user: dict = Depends(current_user)) -> dict:
    """Guard every administrative route.

    The role is read from the signed token, never from the request body, so a
    client cannot promote itself by sending `{"isAdmin": true}`.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return user
