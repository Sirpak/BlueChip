"""CLI: build Game Intelligence Packages from the weekly desk."""

from __future__ import annotations

import argparse
import json
import logging

from app.services.intelligence.package import build_from_weekly


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build cached Game Intelligence Packages")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = build_from_weekly(use_llm=not args.no_llm, limit=args.limit, force=args.force)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
