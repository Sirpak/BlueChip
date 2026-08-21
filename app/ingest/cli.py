"""CLI: python -m app.ingest --season 2024 [--from-season 1999 --to-season 2025]."""

from __future__ import annotations

import argparse
import logging
import sys

from app.config import get_settings
from app.ingest.identity import backfill_contract
from app.ingest.nflfastr import ingest_season
from app.ingest.schedules import ingest_schedules
from db.session import get_session_factory


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.ingest",
        description="BlueChipWager data ingestion (nflfastR first).",
    )
    parser.add_argument(
        "--season",
        type=int,
        action="append",
        help="NFL season year to ingest (repeatable). Example: --season 2023 --season 2024",
    )
    parser.add_argument(
        "--from-season",
        type=int,
        help="Inclusive start year (use with --to-season). Ingest is 1999–present.",
    )
    parser.add_argument(
        "--to-season",
        type=int,
        help="Inclusive end year.",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download parquet even if cached under data/raw/",
    )
    parser.add_argument(
        "--backfill-contract",
        action="store_true",
        help="Seed leagues/teams/players and Market 0 snapshots without ingesting PBP.",
    )
    parser.add_argument(
        "--schedules",
        action="store_true",
        help="Ingest nflverse schedules (kickoff, rest, moneylines, external ids).",
    )
    parser.add_argument(
        "--league",
        default="nfl",
        help="Only nfl is implemented. cfb is rejected until NFL gates pass.",
    )
    return parser


def _seasons(args: argparse.Namespace) -> list[int]:
    years: set[int] = set(args.season or [])
    if args.from_season is not None or args.to_season is not None:
        if args.from_season is None or args.to_season is None:
            raise SystemExit("--from-season and --to-season must be used together")
        if args.to_season < args.from_season:
            raise SystemExit("--to-season must be >= --from-season")
        years.update(range(args.from_season, args.to_season + 1))
    return sorted(years)


def _pbp_seasons(args: argparse.Namespace) -> list[int]:
    """PBP years. --schedules with only --from-season/--to-season does not re-pull PBP."""
    if args.schedules and not args.season:
        return []
    return _seasons(args)


def _schedule_window(args: argparse.Namespace, pbp_years: list[int]) -> tuple[int, int]:
    from_season = args.from_season if args.from_season is not None else 1999
    to_season = args.to_season if args.to_season is not None else 2025
    if pbp_years and args.from_season is None:
        from_season = min(pbp_years)
    if pbp_years and args.to_season is None:
        to_season = max(pbp_years)
    if to_season < from_season:
        raise SystemExit("--to-season must be >= --from-season")
    return from_season, to_season


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if str(args.league).lower() != "nfl":
        print("CFB ingest is locked until NFL v0.1 gates pass.", file=sys.stderr)
        return 2

    seasons = _pbp_seasons(args)
    if not seasons and not args.backfill_contract and not args.schedules:
        print(
            "Pass --season, --from-season/--to-season, --schedules, and/or --backfill-contract.",
            file=sys.stderr,
        )
        return 2

    settings = get_settings()
    _configure_logging(settings.log_level)

    from db.base import Base
    from db.session import get_engine

    Base.metadata.create_all(bind=get_engine())
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)

    session = get_session_factory()()
    try:
        for season in seasons:
            stats = ingest_season(
                session,
                season,
                force_download=args.force_download,
            )
            print(
                f"season={stats['season']} "
                f"games={stats['games_in_db']} "
                f"plays={stats['plays_in_db']}"
            )
        if args.schedules:
            from_season, to_season = _schedule_window(args, seasons)
            sched = ingest_schedules(
                session,
                from_season=from_season,
                to_season=to_season,
                force_download=args.force_download,
            )
            print(
                "schedules "
                f"updated={sched['updated']} "
                f"inserted={sched['inserted']} "
                f"conflicts={sched['conflicts']} "
                f"kickoff={sched['games_with_kickoff']} "
                f"rest={sched['games_with_rest']}"
            )
        contract = backfill_contract(session)
        print(
            "contract "
            f"teams_new={contract['teams_new']} "
            f"players_new={contract['players_new']} "
            f"market_rows={contract['market_rows']}"
        )
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
