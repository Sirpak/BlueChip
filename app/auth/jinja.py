"""Jinja helpers — UX only. Backend still enforces entitlements."""

from __future__ import annotations

from app.auth.entitlements import has_entitlement
from db.models import User


def can_factory(user: User | None):
    def can(name: str) -> bool:
        if user is None:
            return False
        plan = getattr(user, "plan", None) or "FREE"
        return has_entitlement(user.role, plan, name)

    return can


def auth_template_context(user: User | None) -> dict:
    return {"can": can_factory(user), "current_user": user}
