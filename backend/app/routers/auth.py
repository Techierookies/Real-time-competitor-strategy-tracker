"""Signup, login and identity."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import Settings, get_settings
from ..db import Database
from ..deps import get_db
from ..schemas import LoginRequest, SignupRequest, TokenResponse
from ..security import (
    create_access_token,
    current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(
    payload: SignupRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Create an account.

    Role is always 'user'. The previous implementation let the request body
    choose its own role, so anyone could sign up as an administrator.
    """
    try:
        with db.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, 'user')
                """,
                (payload.name, payload.email, hash_password(payload.password)),
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        ) from error

    token = create_access_token(payload.email, "user", settings)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_minutes,
        name=payload.name,
        email=payload.email,
        role="user",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    with db.connect() as connection:
        row = connection.execute(
            "SELECT name, email, password_hash, role FROM users WHERE email = ?",
            (payload.email,),
        ).fetchone()

    # One message for both "no such user" and "wrong password", so the endpoint
    # cannot be used to enumerate which email addresses have accounts.
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token(row["email"], row["role"], settings)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_minutes,
        name=row["name"],
        email=row["email"],
        role=row["role"],
    )


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user
