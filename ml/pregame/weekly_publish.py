"""CLI: publish Week 1 desk cards with confidence %."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from app.services.weekly_desk import publish_weekly


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish Week 1 NFL/CFB desk cards (0 = all week 1)")
    parser.add_argument("--nfl", type=int, default=0, help="NFL Week 1 count (0 = all)")
    parser.add_argument("--cfb", type=int, default=0, help="CFB Week 1 count (0 = all)")
    parser.add_argument("--ai-top", type=int, default=8, help="Enrich top-N by confidence with LLM news")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    payload = publish_weekly(nfl_n=args.nfl, cfb_n=args.cfb, ai_top=args.ai_top)
    best = payload.get("highest_confidence_cfb_week1") or payload.get("highest_confidence")
    print(
        json.dumps(
            {
                "published_at": payload["published_at"],
                "counts": payload["counts"],
                "highest_confidence_cfb_week1": best,
                "path": "data/weekly/BCW-WEEKLY-DESK.json",
                "top5": [
                    {
                        "league": c["league"],
                        "matchup": c["matchup"],
                        "lean": c["ai"]["recommendation_team"],
                        "confidence_pct": c["projection"]["confidence_pct"],
                        "ai": c["ai"]["provider"],
                    }
                    for c in payload["cards"][:5]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
