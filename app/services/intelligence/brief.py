"""AI writer for Game Intelligence Brief — explains evidence; does not invent stats."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

AI_MODEL_GEMINI = "gemini-flash-latest"
AI_MODEL_OPENROUTER = "openai/gpt-oss-20b:free"


def _fallback_brief(evidence: dict[str, Any]) -> dict[str, str]:
    g = evidence["game"]
    lean = evidence.get("lean_team") or g["home_team"]
    edges = evidence.get("headline_cards") or []
    top = edges[0]["fan_line"] if edges else "Overall team strength is the clearest signal."
    paths = evidence.get("paths") or {}
    risks = evidence.get("risks") or []
    events = evidence.get("events") or []
    changed = "\n".join(f"• {e['structured_fact']}" for e in events[:4]) or "• No material sourced events ranked yet."
    market = g.get("spread_label") or "pick'em"
    mu = evidence.get("projection", {}).get("mu_home")
    mu_txt = f"BCW desk μ (home): {mu:+.1f} (Research Preview)" if mu is not None else "BCW-RIDGE snapshot: pending"
    short = f"BlueChip leans {lean}. Top signal: {top}"
    full = (
        f"{g.get('away_name') or g['away_team']} at {g.get('home_name') or g['home_team']}.\n\n"
        f"BlueChip leans {lean}. {top}\n\n"
        f"Why {lean} has the edge\n"
        + "\n".join(f"- {c['fan_line']}" for c in edges[:3])
        + f"\n\nBlueChip projection\nMarket: {market}\n{mu_txt}\n"
        f"Win probability: unavailable until probability model passes validation.\n\n"
        f"How each team wins\n"
        f"{g['home_team']}: {paths.get('home', '')}\n"
        f"{g['away_team']}: {paths.get('away', '')}\n\n"
        f"What changed this week\n{changed}\n\n"
        f"What could make BlueChip wrong?\n"
        + "\n".join(f"• {r}" for r in risks)
        + f"\n\nBottom line: {lean} has more ways to win on the current MATCHUP SIGNAL board, "
        f"but football variance (turnovers, explosives) remains large around any margin estimate."
    )
    return {"summary_short": short, "summary_full": full}


def write_brief(evidence: dict[str, Any], *, use_llm: bool = True) -> dict[str, Any]:
    settings = get_settings()
    prompt = (
        "You are BlueChip's Game Intelligence writer. Explain this matchup to a football fan. "
        "Do NOT invent statistics, injuries, or weather. Use ONLY the JSON evidence. "
        "Distinguish BlueChip quantitative MATCHUP SIGNAL findings from sourced reporting. "
        "Write sections: Bottom line (2-3 sentences), Why the lean has the edge (bullet edges), "
        "How each team wins, What changed this week (from events only), "
        "What could make BlueChip wrong, Final bottom line. "
        "Mention that win probability is unpublished until validation. Keep under 350 words.\n\n"
        f"EVIDENCE:\n{evidence}"
    )
    text = None
    provider = "fallback"
    model = "desk-template"
    if use_llm and settings.google_studio_api_key:
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{AI_MODEL_GEMINI}:generateContent"
            )
            with httpx.Client(timeout=60.0) as client:
                r = client.post(
                    url,
                    headers={"Content-Type": "application/json", "x-goog-api-key": settings.google_studio_api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 700},
                    },
                )
                if r.status_code < 400:
                    parts = r.json()["candidates"][0]["content"]["parts"]
                    text = "".join(p.get("text", "") for p in parts).strip()
                    provider = "google"
                    model = AI_MODEL_GEMINI
        except Exception:
            logger.exception("Brief Gemini failed")
    if text is None and use_llm and settings.openrouter_api_key:
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": AI_MODEL_OPENROUTER,
                        "messages": [
                            {"role": "system", "content": "Explain only from supplied football evidence."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.4,
                        "max_tokens": 700,
                    },
                )
                if r.status_code < 400:
                    text = r.json()["choices"][0]["message"]["content"].strip()
                    provider = "openrouter"
                    model = AI_MODEL_OPENROUTER
        except Exception:
            logger.exception("Brief OpenRouter failed")
    if text is None:
        fb = _fallback_brief(evidence)
        return {**fb, "provider": provider, "model": model}
    short = text.split("\n")[0][:220]
    return {
        "summary_short": short,
        "summary_full": text,
        "provider": provider,
        "model": model,
    }
