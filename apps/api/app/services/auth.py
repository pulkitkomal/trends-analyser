from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from fastapi import Depends, HTTPException, Request, Response
from sqlmodel import Session, select

from app.db import get_session
from app.models import AuthSession, User, utcnow

COOKIE = "sid"
ROUNDS = 200_000
DAYS = 30


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), ROUNDS)
    return f"pbkdf2${ROUNDS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, hexdigest = stored.split("$", 3)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("ascii"), int(rounds)
        )
        return hmac.compare_digest(digest.hex(), hexdigest)
    except ValueError:
        return False


def set_session(response: Response, session: Session, user: User) -> None:
    token = secrets.token_urlsafe(32)
    session.add(
        AuthSession(
            user_id=user.id,  # type: ignore[arg-type]
            token=token,
            expires_at=utcnow() + timedelta(days=DAYS),
        )
    )
    session.commit()
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=DAYS * 24 * 3600,
        path="/",
    )


def clear_session(response: Response, session: Session, token: str | None) -> None:
    if token:
        row = session.exec(select(AuthSession).where(AuthSession.token == token)).first()
        if row:
            session.delete(row)
            session.commit()
    response.delete_cookie(COOKIE, path="/")


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "Sign in to continue")
    row = session.exec(select(AuthSession).where(AuthSession.token == token)).first()
    if not row or row.expires_at < utcnow():
        raise HTTPException(401, "Sign in to continue")
    user = session.get(User, row.user_id)
    if not user:
        raise HTTPException(401, "Sign in to continue")
    return user
