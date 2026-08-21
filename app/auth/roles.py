"""Role and plan enums. Cognito authenticates; this app stores what they bought."""

from __future__ import annotations


class UserRole:
    USER = "USER"
    ADMIN = "ADMIN"


class SubscriptionPlan:
    FREE = "FREE"
    PRO = "PRO"
    RESEARCH = "RESEARCH"
    INTERNAL = "INTERNAL"


PLAN_LABELS = {
    SubscriptionPlan.FREE: "Free Plan",
    SubscriptionPlan.PRO: "Pro Plan",
    SubscriptionPlan.RESEARCH: "Research Plan",
    SubscriptionPlan.INTERNAL: "Internal",
}
