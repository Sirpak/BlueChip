"""Entitlement-gated research/backtest stubs."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.permissions import require_entitlement
from db.models import User

router = APIRouter(tags=["entitlements"])


@router.get("/api/backtests/export")
def export_backtest(_user: User = Depends(require_entitlement("exports"))) -> dict:
    return {
        "status": "ready_later",
        "message": "CSV/Parquet export ships with Research. Entitlement is enforced now.",
    }


@router.get("/api/research/deep")
def deep_research(_user: User = Depends(require_entitlement("deep_research"))) -> dict:
    return {
        "status": "preview",
        "message": "Deep Research is a Research-plan entitlement. No LLM spend yet.",
    }


@router.get("/api/developer/status")
def developer_status(_user: User = Depends(require_entitlement("developer_access"))) -> dict:
    return {"openapi": "/docs", "status": "future"}
