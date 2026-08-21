"""One CFBD API ping — no ingest."""

from __future__ import annotations

import argparse
import sys

import httpx

from app.config import get_settings

CFBD_TEAMS_URL = "https://api.collegefootballdata.com/teams/fbs"


def ping_cfbd() -> dict:
    settings = get_settings()
    key = settings.cfbd_api_key
    if not key:
        return {"ok": False, "error": "CFBD_API_KEY not set in .env"}
    headers = {"Authorization": f"Bearer {key}"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(CFBD_TEAMS_URL, headers=headers)
    if resp.status_code != 200:
        return {"ok": False, "status": resp.status_code, "body": resp.text[:500]}
    teams = resp.json()
    return {"ok": True, "status": resp.status_code, "fbs_teams": len(teams)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingest.cfbd_ping")
    args = parser.parse_args(argv)
    result = ping_cfbd()
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
