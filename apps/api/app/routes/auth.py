from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.models import AuthSession, Topic, User
from app.services.auth import (
    COOKIE,
    clear_session,
    current_user,
    hash_password,
    set_session,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=8, max_length=200)


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    name: str


class UserPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)


def _email(value: str) -> str:
    return value.strip().lower()


@router.post("/register", response_model=UserOut)
def register(body: RegisterIn, response: Response, session: Session = Depends(get_session)) -> User:
    email = _email(body.email)
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Enter a valid email")
    if session.exec(select(User).where(User.email == email)).first():
        raise HTTPException(409, "That email is already in use")
    first = session.exec(select(User).limit(1)).first() is None
    user = User(email=email, name=body.name.strip(), password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    if first:
        for topic in session.exec(select(Topic).where(Topic.user_id == None)).all():  # noqa: E711
            topic.user_id = user.id
            session.add(topic)
        session.commit()
    set_session(response, session, user)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, response: Response, session: Session = Depends(get_session)) -> User:
    user = session.exec(select(User).where(User.email == _email(body.email))).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is wrong")
    set_session(response, session, user)
    return user


@router.post("/logout")
def logout(request: Request, response: Response, session: Session = Depends(get_session)) -> dict:
    clear_session(response, session, request.cookies.get(COOKIE))
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UserPatch, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> User:
    if body.name:
        user.name = body.name.strip()
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


@router.delete("/me")
def delete_me(
    response: Response,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> dict:
    from app.models import Comment, Digest, InterestPoint, KeywordStat, LlmReport, Post, Surface

    for topic in session.exec(select(Topic).where(Topic.user_id == user.id)).all():
        for model in (LlmReport, Digest, InterestPoint, KeywordStat, Comment, Post, Surface):
            for row in session.exec(select(model).where(model.topic_id == topic.id)).all():  # type: ignore[attr-defined]
                session.delete(row)
        session.delete(topic)
    for row in session.exec(select(AuthSession).where(AuthSession.user_id == user.id)).all():
        session.delete(row)
    session.delete(user)
    session.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}
