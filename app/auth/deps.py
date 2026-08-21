"""Auth dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.tokens import load_session_token
from app.config import get_settings
from db.models import User
from db.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def _user_from_cookie(session: Session, token: str | None) -> User | None:
    if not token:
        return None
    payload = load_session_token(token)
    if not payload:
        return None
    user_id = payload.get("uid")
    if user_id is None:
        return None
    user = session.get(User, int(user_id))
    if user is None or not user.is_active:
        return None
    return user


def get_optional_user(
    session: SessionDep,
    bcw_session: Annotated[str | None, Cookie(alias="bcw_session")] = None,
) -> User | None:
    return _user_from_cookie(session, bcw_session)


def require_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_admin(user: Annotated[User, Depends(require_user)]) -> User:
    if user.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


UserDep = Annotated[User, Depends(require_user)]
AdminDep = Annotated[User, Depends(require_admin)]
