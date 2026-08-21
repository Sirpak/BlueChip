"""Idempotent local development accounts (hashed passwords)."""

from __future__ import annotations

import logging
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, verify_password
from app.auth.roles import SubscriptionPlan, UserRole
from app.config import get_settings
from db.models import User

logger = logging.getLogger(__name__)


class SeedAccount(NamedTuple):
    username: str
    password: str
    display_name: str
    role: str
    plan: str
    email: str


def dev_accounts() -> list[SeedAccount]:
    s = get_settings()
    accounts = [
        SeedAccount(
            s.auth_free_username,
            s.auth_free_password,
            "Demo Free",
            UserRole.USER,
            SubscriptionPlan.FREE,
            "demo_free@local.dev",
        ),
        SeedAccount(
            s.auth_pro_username,
            s.auth_pro_password,
            "Demo Pro",
            UserRole.USER,
            SubscriptionPlan.PRO,
            "demo_pro@local.dev",
        ),
        SeedAccount(
            s.auth_research_username,
            s.auth_research_password,
            "Demo Research",
            UserRole.USER,
            SubscriptionPlan.RESEARCH,
            "demo_research@local.dev",
        ),
        SeedAccount(
            s.auth_admin_username,
            s.auth_admin_password,
            "Administrator",
            UserRole.ADMIN,
            SubscriptionPlan.INTERNAL,
            "admin@local.dev",
        ),
    ]
    if s.auth_demo_username and s.auth_demo_password:
        accounts.append(
            SeedAccount(
                s.auth_demo_username,
                s.auth_demo_password,
                s.auth_demo_username,
                UserRole.USER,
                SubscriptionPlan.FREE,
                f"{s.auth_demo_username}@local.dev",
            )
        )
    return accounts


def upsert_user(session: Session, account: SeedAccount) -> User:
    row = session.query(User).filter(User.username == account.username).one_or_none()
    if row is None:
        row = User(
            username=account.username,
            email=account.email,
            password_hash=hash_password(account.password),
            display_name=account.display_name,
            role=account.role,
            plan=account.plan,
            is_active=True,
            email_verified=True,
        )
        session.add(row)
        logger.info("Seeded %s/%s user %r", account.role, account.plan, account.username)
        return row
    row.email = account.email
    row.display_name = account.display_name
    row.role = account.role
    row.plan = account.plan
    row.is_active = True
    if not verify_password(account.password, row.password_hash):
        row.password_hash = hash_password(account.password)
    logger.info("Updated seed user %r (%s/%s)", account.username, account.role, account.plan)
    return row


def seed_dev_users(session: Session) -> None:
    for account in dev_accounts():
        upsert_user(session, account)
    session.commit()
