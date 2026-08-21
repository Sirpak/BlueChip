"""Read-only queries for the browser dashboard and JSON API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class SeasonCounts:
    season: int
    games: int
    plays: int
    regular: int
    postseason: int


@dataclass(frozen=True)
class Standing:
    team: str
    wins: int
    losses: int
    ties: int
    ppg: float
    papg: float
    diff: float
    off_epa: float | None
    def_epa: float | None
    pass_epa: float | None
    rush_epa: float | None

    @property
    def net_epa(self) -> float | None:
        if self.off_epa is None or self.def_epa is None:
            return None
        return self.off_epa - self.def_epa

    @property
    def record(self) -> str:
        if self.ties:
            return f"{self.wins}-{self.losses}-{self.ties}"
        return f"{self.wins}-{self.losses}"


def _rows(session: Session, sql: str, **params: Any) -> list[Any]:
    return list(session.execute(text(sql), params))


def latest_season(session: Session) -> int | None:
    value = session.execute(text("SELECT MAX(season) FROM games")).scalar()
    return int(value) if value is not None else None


def inventory(session: Session) -> list[SeasonCounts]:
    sql = """
        SELECT
            g.season,
            COUNT(DISTINCT g.game_id) AS games,
            SUM(CASE WHEN g.season_type = 'REG' THEN 1 ELSE 0 END) AS regular,
            SUM(CASE WHEN g.season_type = 'POST' THEN 1 ELSE 0 END) AS postseason,
            (SELECT COUNT(*) FROM plays p WHERE p.season = g.season) AS plays
        FROM games g
        GROUP BY g.season
        ORDER BY g.season
    """
    return [
        SeasonCounts(
            season=int(r.season),
            games=int(r.games),
            plays=int(r.plays or 0),
            regular=int(r.regular or 0),
            postseason=int(r.postseason or 0),
        )
        for r in _rows(session, sql)
    ]


def scoring_summary(session: Session, season: int) -> dict[str, Any]:
    sql = """
        SELECT
            COUNT(*) AS n,
            SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS home_wins,
            SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) AS away_wins,
            SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS ties,
            AVG(total) AS avg_total,
            AVG(home_score) AS avg_home,
            AVG(away_score) AS avg_away
        FROM games
        WHERE season = :season
          AND season_type = 'REG'
          AND home_score IS NOT NULL
    """
    row = session.execute(text(sql), {"season": season}).one()
    n = int(row.n or 0)
    home_wins = int(row.home_wins or 0)
    return {
        "games": n,
        "home_wins": home_wins,
        "away_wins": int(row.away_wins or 0),
        "ties": int(row.ties or 0),
        "home_win_rate": (home_wins / n) if n else None,
        "avg_total": float(row.avg_total) if row.avg_total is not None else None,
        "avg_home": float(row.avg_home) if row.avg_home is not None else None,
        "avg_away": float(row.avg_away) if row.avg_away is not None else None,
    }


def weekly_scoring(session: Session, season: int) -> list[dict[str, Any]]:
    sql = """
        SELECT
            week,
            COUNT(*) AS games,
            AVG(total) AS avg_total,
            SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS home_wins
        FROM games
        WHERE season = :season
          AND season_type = 'REG'
          AND home_score IS NOT NULL
        GROUP BY week
        ORDER BY week
    """
    return [
        {
            "week": int(r.week),
            "games": int(r.games),
            "avg_total": round(float(r.avg_total), 1) if r.avg_total is not None else None,
            "home_wins": int(r.home_wins or 0),
        }
        for r in _rows(session, sql, season=season)
    ]


def _epa_maps(session: Session, season: int) -> tuple[dict[str, Any], dict[str, Any]]:
    off_sql = """
        SELECT
            posteam AS team,
            AVG(epa) AS off_epa,
            AVG(CASE WHEN pass_attempt = 1 THEN epa END) AS pass_epa,
            AVG(CASE WHEN rush_attempt = 1 THEN epa END) AS rush_epa
        FROM plays
        WHERE season = :season
          AND season_type = 'REG'
          AND posteam IS NOT NULL
          AND play_type IN ('pass', 'run')
          AND epa IS NOT NULL
        GROUP BY posteam
    """
    def_sql = """
        SELECT defteam AS team, AVG(epa) AS def_epa
        FROM plays
        WHERE season = :season
          AND season_type = 'REG'
          AND defteam IS NOT NULL
          AND play_type IN ('pass', 'run')
          AND epa IS NOT NULL
        GROUP BY defteam
    """
    offense = {
        r.team: {
            "off_epa": float(r.off_epa) if r.off_epa is not None else None,
            "pass_epa": float(r.pass_epa) if r.pass_epa is not None else None,
            "rush_epa": float(r.rush_epa) if r.rush_epa is not None else None,
        }
        for r in _rows(session, off_sql, season=season)
        if r.team
    }
    defense = {
        r.team: float(r.def_epa) if r.def_epa is not None else None
        for r in _rows(session, def_sql, season=season)
        if r.team
    }
    return offense, defense


def standings(session: Session, season: int) -> list[Standing]:
    sql = """
        WITH teams AS (
            SELECT
                home_team AS team,
                CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS w,
                CASE WHEN home_score < away_score THEN 1 ELSE 0 END AS l,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS t,
                home_score AS pf,
                away_score AS pa
            FROM games
            WHERE season = :season
              AND season_type = 'REG'
              AND home_score IS NOT NULL
            UNION ALL
            SELECT
                away_team,
                CASE WHEN away_score > home_score THEN 1 ELSE 0 END,
                CASE WHEN away_score < home_score THEN 1 ELSE 0 END,
                CASE WHEN away_score = home_score THEN 1 ELSE 0 END,
                away_score,
                home_score
            FROM games
            WHERE season = :season
              AND season_type = 'REG'
              AND home_score IS NOT NULL
        )
        SELECT
            team,
            SUM(w) AS wins,
            SUM(l) AS losses,
            SUM(t) AS ties,
            AVG(pf) AS ppg,
            AVG(pa) AS papg,
            AVG(pf - pa) AS diff
        FROM teams
        GROUP BY team
        ORDER BY wins DESC, diff DESC
    """
    offense, defense = _epa_maps(session, season)
    out: list[Standing] = []
    for r in _rows(session, sql, season=season):
        off = offense.get(r.team, {})
        out.append(
            Standing(
                team=str(r.team),
                wins=int(r.wins),
                losses=int(r.losses),
                ties=int(r.ties),
                ppg=round(float(r.ppg), 1),
                papg=round(float(r.papg), 1),
                diff=round(float(r.diff), 1),
                off_epa=off.get("off_epa"),
                def_epa=defense.get(r.team),
                pass_epa=off.get("pass_epa"),
                rush_epa=off.get("rush_epa"),
            )
        )
    return out


def playoff_games(session: Session, season: int) -> list[dict[str, Any]]:
    sql = """
        SELECT
            game_id, week, game_date, away_team, home_team,
            away_score, home_score, spread_line, total_line
        FROM games
        WHERE season = :season AND season_type = 'POST'
        ORDER BY week, game_date, game_id
    """
    return [_game_dict(r) for r in _rows(session, sql, season=season)]


def upcoming_games(session: Session, *, as_of: date | None = None) -> list[dict[str, Any]]:
    as_of = as_of or date.today()
    sql = """
        SELECT
            game_id, season, week, season_type, game_date, away_team, home_team,
            away_score, home_score, spread_line, total_line
        FROM games
        WHERE game_date >= :as_of
        ORDER BY game_date, game_id
        LIMIT 32
    """
    return [_game_dict(r) for r in _rows(session, sql, as_of=as_of.isoformat())]


def recent_games(session: Session, *, limit: int = 16) -> list[dict[str, Any]]:
    sql = """
        SELECT
            game_id, season, week, season_type, game_date, away_team, home_team,
            away_score, home_score, spread_line, total_line
        FROM games
        WHERE home_score IS NOT NULL
        ORDER BY game_date DESC, week DESC, game_id DESC
        LIMIT :limit
    """
    return [_game_dict(r) for r in _rows(session, sql, limit=limit)]


def team_ratings(session: Session, team: str, season: int) -> dict[str, Any] | None:
    team = team.upper()
    rows = standings(session, season)
    match = next((row for row in rows if row.team == team), None)
    if match is None:
        return None
    payload = asdict(match)
    payload["record"] = match.record
    payload["net_epa"] = match.net_epa
    payload["season"] = season
    return payload


def dashboard_payload(session: Session) -> dict[str, Any]:
    season = latest_season(session)
    counts = inventory(session)
    totals = {
        "games": sum(c.games for c in counts),
        "plays": sum(c.plays for c in counts),
        "seasons": [c.season for c in counts],
    }
    if season is None:
        return {
            "latest_season": None,
            "inventory": [],
            "totals": totals,
            "scoring": None,
            "weekly_scoring": [],
            "standings": [],
            "playoffs": [],
            "upcoming": [],
            "recent": [],
        }

    table = standings(session, season)
    return {
        "latest_season": season,
        "inventory": [asdict(c) for c in counts],
        "totals": totals,
        "scoring": scoring_summary(session, season),
        "weekly_scoring": weekly_scoring(session, season),
        "standings": [_standing_dict(row) for row in table],
        "playoffs": playoff_games(session, season),
        "upcoming": upcoming_games(session),
        "recent": recent_games(session),
    }


def _standing_dict(row: Standing) -> dict[str, Any]:
    payload = asdict(row)
    payload["record"] = row.record
    payload["net_epa"] = row.net_epa
    return payload


def _game_dict(r: Any) -> dict[str, Any]:
    game_date = r.game_date
    if hasattr(game_date, "isoformat"):
        game_date = game_date.isoformat()
    round_label = _round_label(getattr(r, "season_type", None), int(r.week))
    return {
        "game_id": r.game_id,
        "season": int(r.season) if hasattr(r, "season") and r.season is not None else None,
        "week": int(r.week),
        "season_type": getattr(r, "season_type", None),
        "round": round_label,
        "game_date": game_date,
        "away_team": r.away_team,
        "home_team": r.home_team,
        "away_score": r.away_score,
        "home_score": r.home_score,
        "spread_line": float(r.spread_line) if r.spread_line is not None else None,
        "total_line": float(r.total_line) if r.total_line is not None else None,
    }


def _round_label(season_type: str | None, week: int) -> str:
    if season_type != "POST":
        return f"Week {week}"
    labels = {
        19: "Wild card",
        20: "Divisional",
        21: "Conference",
        22: "Super Bowl",
    }
    return labels.get(week, f"Post week {week}")
