"""Monthly plan usage helpers."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.auth.entitlements import PLAN_LIMITS, ask_limit
from app.auth.roles import SubscriptionPlan
from db.models import PlanUsage, User


def _period_bounds(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    start = today.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def current_usage(session: Session, user: User) -> PlanUsage:
    start, end = _period_bounds()
    row = (
        session.query(PlanUsage)
        .filter(
            PlanUsage.user_id == user.id,
            PlanUsage.billing_period_start == start,
        )
        .one_or_none()
    )
    if row is None:
        row = PlanUsage(
            user_id=user.id,
            billing_period_start=start,
            billing_period_end=end,
            ai_queries_used=0,
            ai_credits_used=0,
            exports_used=0,
            deep_research_used=0,
        )
        session.add(row)
        session.flush()
    return row


def usage_payload(session: Session, user: User) -> dict:
    row = current_usage(session, user)
    plan = getattr(user, "plan", None) or SubscriptionPlan.FREE
    limit = ask_limit(plan, user.role)
    remaining = max(0, limit - int(row.ai_queries_used or 0))
    return {
        "plan": plan,
        "billing_period_start": row.billing_period_start.isoformat(),
        "billing_period_end": row.billing_period_end.isoformat(),
        "ask_queries_used": int(row.ai_queries_used or 0),
        "ask_queries_limit": limit,
        "ask_queries_remaining": remaining,
        "exports_used": int(row.exports_used or 0),
        "exports_limit": PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE])["exports"],
        "deep_research_used": int(row.deep_research_used or 0),
        "deep_research_limit": PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE])["deep_research"],
    }


def consume_ask(session: Session, user: User) -> dict:
    row = current_usage(session, user)
    payload = usage_payload(session, user)
    if payload["ask_queries_remaining"] <= 0:
        return {**payload, "allowed": False}
    row.ai_queries_used = int(row.ai_queries_used or 0) + 1
    session.flush()
    out = usage_payload(session, user)
    out["allowed"] = True
    return out
