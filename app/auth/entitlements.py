"""Single source of truth for plan entitlements and temporary AI quotas."""

from __future__ import annotations

from app.auth.roles import SubscriptionPlan, UserRole

PLAN_ENTITLEMENTS: dict[str, frozenset[str]] = {
    SubscriptionPlan.FREE: frozenset(
        {
            "dashboard",
            "games",
            "teams_basic",
            "models_basic",
            "ask_bluechip_limited",
            "research_preview",
            "backtests_preview",
        }
    ),
    SubscriptionPlan.PRO: frozenset(
        {
            "dashboard",
            "games",
            "teams_full",
            "models_full",
            "markets",
            "research",
            "ask_bluechip",
            "citations",
            "historical_search",
            "backtests_standard",
        }
    ),
    SubscriptionPlan.RESEARCH: frozenset(
        {
            "dashboard",
            "games",
            "teams_full",
            "models_full",
            "markets",
            "research",
            "ask_bluechip",
            "citations",
            "historical_search",
            "backtests_standard",
            "backtests_advanced",
            "exports",
            "deep_research",
            "developer_access",
        }
    ),
    SubscriptionPlan.INTERNAL: frozenset({"*"}),
}

PLAN_LIMITS: dict[str, dict[str, int]] = {
    SubscriptionPlan.FREE: {"ask_queries": 10, "exports": 0, "deep_research": 0},
    SubscriptionPlan.PRO: {"ask_queries": 200, "exports": 0, "deep_research": 0},
    SubscriptionPlan.RESEARCH: {"ask_queries": 750, "exports": 50, "deep_research": 25},
    SubscriptionPlan.INTERNAL: {"ask_queries": 10_000, "exports": 10_000, "deep_research": 10_000},
}


def entitlements_for(role: str, plan: str) -> frozenset[str]:
    if role == UserRole.ADMIN:
        return frozenset({"*"})
    return PLAN_ENTITLEMENTS.get(plan, PLAN_ENTITLEMENTS[SubscriptionPlan.FREE])


def has_entitlement(role: str, plan: str, name: str) -> bool:
    held = entitlements_for(role, plan)
    if "*" in held:
        return True
    aliases = {
        "teams_full": {"teams_basic"},
        "models_full": {"models_basic"},
        "research": {"research_preview"},
        "backtests_standard": {"backtests_preview"},
        "backtests_advanced": {"backtests_standard", "backtests_preview"},
        "ask_bluechip": {"ask_bluechip_limited"},
    }
    if name in held:
        return True
    # Broader grants include narrower ones
    if name == "ask_bluechip_limited" and "ask_bluechip" in held:
        return True
    if name == "models_basic" and "models_full" in held:
        return True
    if name == "teams_basic" and "teams_full" in held:
        return True
    if name == "research_preview" and "research" in held:
        return True
    if name == "backtests_preview" and ("backtests_standard" in held or "backtests_advanced" in held):
        return True
    if name == "backtests_standard" and "backtests_advanced" in held:
        return True
    _ = aliases
    return False


def ask_limit(plan: str, role: str) -> int:
    if role == UserRole.ADMIN:
        return PLAN_LIMITS[SubscriptionPlan.INTERNAL]["ask_queries"]
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[SubscriptionPlan.FREE])["ask_queries"]
