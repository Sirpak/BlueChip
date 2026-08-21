"""Signed session tokens (local auth; replace with Cognito JWT later)."""

from __future__ import annotations

from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.auth_secret_key, salt="bcw-session")


def create_session_token(payload: dict[str, Any]) -> str:
    return _serializer().dumps(payload)


def load_session_token(token: str, *, max_age: int | None = None) -> dict[str, Any] | None:
    settings = get_settings()
    age = max_age if max_age is not None else settings.auth_token_max_age
    try:
        data = _serializer().loads(token, max_age=age)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict):
        return None
    return data
