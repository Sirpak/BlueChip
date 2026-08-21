"""Authentication API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import get_optional_user, require_user
from app.auth.entitlements import entitlements_for, has_entitlement
from app.auth.passwords import verify_password
from app.auth.roles import PLAN_LABELS
from app.auth.tokens import create_session_token
from app.auth.usage import usage_payload
from app.config import get_settings
from db.models import User
from db.session import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    display_name: str
    role: str
    plan: str
    plan_label: str
    initials: str
    entitlements: list[str]
    usage: dict


def _initials(user: User) -> str:
    name = user.display_name or user.username
    parts = name.replace("_", " ").replace(".", " ").split()
    return "".join(p[0].upper() for p in parts[:2] if p) or user.username[:2].upper()


def user_out(session: Session, user: User) -> UserOut:
    plan = getattr(user, "plan", None) or "FREE"
    held = sorted(entitlements_for(user.role, plan))
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name or user.username,
        role=user.role,
        plan=plan,
        plan_label=PLAN_LABELS.get(plan, plan),
        initials=_initials(user),
        entitlements=held,
        usage=usage_payload(session, user),
    )


@router.post("/login")
def login(
    body: LoginBody,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
) -> UserOut:
    user = session.query(User).filter(User.username == body.username).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    user.last_login_at = datetime.now(timezone.utc)
    token = create_session_token({"uid": user.id, "role": user.role, "plan": getattr(user, "plan", "FREE")})
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.auth_token_max_age,
        path="/",
    )
    return user_out(session, user)


@router.post("/logout")
def logout(response: Response) -> dict[str, str]:
    settings = get_settings()
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User | None, Depends(get_optional_user)],
) -> UserOut:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user_out(session, user)


@router.get("/usage")
def usage(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(require_user)],
) -> dict:
    return usage_payload(session, user)
