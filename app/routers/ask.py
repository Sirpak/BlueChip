"""Ask BlueChip quota + stub answers (no OpenAI yet)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.deps import UserDep
from app.auth.entitlements import has_entitlement
from app.auth.usage import consume_ask
from db.session import get_session

router = APIRouter(prefix="/api/ask", tags=["ask"])


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@router.post("/query")
def ask_query(body: AskBody, session: Session = Depends(get_session), user: UserDep = ...) -> dict:
    plan = getattr(user, "plan", None) or "FREE"
    if not (
        has_entitlement(user.role, plan, "ask_bluechip")
        or has_entitlement(user.role, plan, "ask_bluechip_limited")
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="upgrade_required")
    meter = consume_ask(session, user)
    if not meter["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "quota_exceeded", "usage": meter},
        )
    return {
        "question": body.question,
        "answer": (
            "Ask BlueChip retrieves saved model output. Cover percentages are not published yet. "
            "BCW-RIDGE-v0.1 is a Research Preview margin candidate trained on 2009–2022 only."
        ),
        "sources": ["Walk-forward artifact", "Stern conversion engine", "v0.1 freeze protocol"],
        "usage": meter,
    }
