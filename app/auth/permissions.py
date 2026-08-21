"""FastAPI entitlement guards. 401 unauthenticated, 403 authenticated-but-denied."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.deps import require_user
from app.auth.entitlements import has_entitlement
from app.auth.roles import UserRole
from db.models import User


def require_entitlement(name: str) -> Callable[[User], User]:
    def _inner(user: Annotated[User, Depends(require_user)]) -> User:
        plan = getattr(user, "plan", None) or "FREE"
        if not has_entitlement(user.role, plan, name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "upgrade_required", "entitlement": name, "plan": plan},
            )
        return user

    _inner.__name__ = f"require_{name}"
    return _inner


def require_admin(user: Annotated[User, Depends(require_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def require_plan(*plans: str) -> Callable[[User], User]:
    wanted = {p.upper() for p in plans}

    def _inner(user: Annotated[User, Depends(require_user)]) -> User:
        if user.role == UserRole.ADMIN:
            return user
        plan = getattr(user, "plan", None) or "FREE"
        if plan not in wanted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "upgrade_required", "plan": plan, "required": sorted(wanted)},
            )
        return user

    return _inner
