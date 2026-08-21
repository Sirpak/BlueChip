"""ORM models for BlueChipWager core tables."""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class League(Base, TimestampMixin):
    """NFL | CFB. Exists from day one so CFB does not rewrite the schema."""

    __tablename__ = "leagues"

    league_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)


class Team(Base, TimestampMixin):
    """Internal team identity. Join on this, not on display names."""

    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("league", "abbreviation", name="uq_teams_league_abbr"),)

    team_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league: Mapped[str] = mapped_column(String(8), ForeignKey("leagues.league_id"), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    conference: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    external_ids: Mapped[list["TeamExternalId"]] = relationship(back_populates="team")


class TeamExternalId(Base, TimestampMixin):
    __tablename__ = "team_external_ids"
    __table_args__ = (UniqueConstraint("system", "external_id", name="uq_team_ext"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=False)
    system: Mapped[str] = mapped_column(String(32), nullable=False)
    # nflverse | espn | cfbd | pfr
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)

    team: Mapped["Team"] = relationship(back_populates="external_ids")


class Player(Base, TimestampMixin):
    __tablename__ = "players"
    __table_args__ = (Index("ix_players_league_name", "league", "canonical_name"),)

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league: Mapped[str] = mapped_column(String(8), ForeignKey("leagues.league_id"), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    external_ids: Mapped[list["PlayerExternalId"]] = relationship(back_populates="player")


class PlayerExternalId(Base, TimestampMixin):
    __tablename__ = "player_external_ids"
    __table_args__ = (UniqueConstraint("system", "external_id", name="uq_player_ext"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False)
    system: Mapped[str] = mapped_column(String(32), nullable=False)
    # gsis | espn | cfbd | pfr
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)

    player: Mapped["Player"] = relationship(back_populates="external_ids")


class Stadium(Base, TimestampMixin):
    """Hardcoded stadium metadata (dome vs outdoor, coordinates)."""

    __tablename__ = "stadiums"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    team_abbr: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    roof: Mapped[str] = mapped_column(String(32), nullable=False, default="outdoor")
    # outdoor | dome | retractable
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Game(Base, TimestampMixin):
    """One NFL game (regular or postseason), keyed by nflverse game_id."""

    __tablename__ = "games"
    __table_args__ = (
        Index("ix_games_season_week", "season", "week"),
        Index("ix_games_kickoff", "kickoff"),
        Index("ix_games_league_season", "league", "season"),
    )

    game_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    # e.g. 2024_01_KC_BAL
    league: Mapped[str] = mapped_column(String(8), nullable=False, default="NFL", server_default="NFL")
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    season_type: Mapped[str] = mapped_column(String(8), nullable=False, default="REG")
    # REG | POST | PRE
    game_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    kickoff: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    home_team: Mapped[str] = mapped_column(String(8), nullable=False)
    away_team: Mapped[str] = mapped_column(String(8), nullable=False)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    roof: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    surface: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stadium_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("stadiums.id"),
        nullable=True,
    )

    result: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # home_score - away_score
    total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spread_line: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_line: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # nflverse schedules (rest / kickoff / historical prices)
    game_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    weekday: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    gametime: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    stadium_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    home_rest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_rest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_moneyline: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_moneyline: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spread_home_odds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    spread_away_odds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    over_odds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    under_odds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overtime: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    div_game: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    neutral_site: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    plays: Mapped[list["Play"]] = relationship(back_populates="game")
    external_ids: Mapped[list["GameExternalId"]] = relationship(back_populates="game")


class GameExternalId(Base, TimestampMixin):
    __tablename__ = "game_external_ids"
    __table_args__ = (
        UniqueConstraint("system", "external_id", name="uq_game_ext"),
        UniqueConstraint("game_id", "system", name="uq_game_ext_system"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("games.game_id", ondelete="CASCADE"),
        nullable=False,
    )
    system: Mapped[str] = mapped_column(String(32), nullable=False)
    # nflverse | espn | pfr | gsis
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)

    game: Mapped["Game"] = relationship(back_populates="external_ids")


class IngestConflict(Base, TimestampMixin):
    """PBP vs schedules (or later sources). Flag; do not silent-overwrite scores."""

    __tablename__ = "ingest_conflicts"
    __table_args__ = (Index("ix_ingest_conflicts_game", "game_id", "field"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(32), ForeignKey("games.game_id"), nullable=False)
    field: Mapped[str] = mapped_column(String(32), nullable=False)
    existing_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    incoming_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    kept: Mapped[str] = mapped_column(String(16), nullable=False, default="existing")
    source_existing: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source_incoming: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class Play(Base, TimestampMixin):
    """Normalized nflfastR play-by-play row (curated columns for modeling)."""

    __tablename__ = "plays"
    __table_args__ = (
        UniqueConstraint("game_id", "play_id", name="uq_plays_game_play"),
        Index("ix_plays_season_week", "season", "week"),
        Index("ix_plays_posteam", "posteam", "season", "week"),
        Index("ix_plays_defteam", "defteam", "season", "week"),
        Index("ix_plays_league_season", "league", "season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    game_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("games.game_id", ondelete="CASCADE"),
        nullable=False,
    )
    play_id: Mapped[str] = mapped_column(String(32), nullable=False)
    # nflfastR play_id is numeric-ish; store as string for safety
    league: Mapped[str] = mapped_column(String(8), nullable=False, default="NFL", server_default="NFL")
    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    season: Mapped[int] = mapped_column(Integer, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    season_type: Mapped[str] = mapped_column(String(8), nullable=False, default="REG")
    game_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    home_team: Mapped[str] = mapped_column(String(8), nullable=False)
    away_team: Mapped[str] = mapped_column(String(8), nullable=False)
    posteam: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    defteam: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    posteam_type: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)

    play_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    down: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ydstogo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    yardline_100: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qtr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quarter_seconds_remaining: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    half_seconds_remaining: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    game_seconds_remaining: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    yards_gained: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    air_yards: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    yards_after_catch: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ep: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    pass_attempt: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    rush_attempt: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    complete_pass: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    incomplete_pass: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    interception: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    touchdown: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    first_down: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    shotgun: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    no_huddle: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    special_teams_play: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    score_differential: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    passer_player_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    passer_player_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rusher_player_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rusher_player_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    game: Mapped["Game"] = relationship(back_populates="plays")


class TeamRating(Base, TimestampMixin):
    """Per-team weekly rating / EPA aggregates (Phase 2)."""

    __tablename__ = "team_ratings"
    __table_args__ = (
        UniqueConstraint("team", "season", "week", "rating_type", name="uq_team_ratings"),
        Index("ix_team_ratings_lookup", "season", "week", "team"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league: Mapped[str] = mapped_column(String(8), nullable=False, default="NFL", server_default="NFL")
    team: Mapped[str] = mapped_column(String(8), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # e.g. off_epa, def_epa, pass_off_epa, ...
    value: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prior_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class OddsSnapshot(Base, TimestampMixin):
    """Market odds at a point in time; de-vig stored at ingest (Phase 1)."""

    __tablename__ = "odds_snapshots"
    __table_args__ = (
        Index("ix_odds_game_book", "game_id", "bookmaker", "market"),
        Index("ix_odds_captured", "captured_at"),
        UniqueConstraint(
            "game_id",
            "market_source",
            "market_type",
            "market",
            "side",
            name="uq_odds_market_snapshot",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league: Mapped[str] = mapped_column(String(8), nullable=False, default="NFL", server_default="NFL")
    game_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("games.game_id"),
        nullable=True,
    )
    # may be null until we map external event ids
    external_event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bookmaker: Mapped[str] = mapped_column(String(64), nullable=False)
    market_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    market_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    # h2h | spreads | totals | spread | total
    side: Mapped[str] = mapped_column(String(32), nullable=False)
    # home | away | over | under | team abbr
    price_american: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price_decimal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # spread / total line
    implied_prob_raw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    implied_prob_devig: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    known_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_closing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class User(Base, TimestampMixin):
    """Local auth user. Cognito later answers who; plan stays in this table."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_users_username"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="USER")
    plan: Mapped[str] = mapped_column(String(16), nullable=False, default="FREE", server_default="FREE")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PlanUsage(Base, TimestampMixin):
    """Per-billing-period meters (Ask queries, exports). Stripe will drive plan; this stores usage."""

    __tablename__ = "plan_usage"
    __table_args__ = (UniqueConstraint("user_id", "billing_period_start", name="uq_plan_usage_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    ai_queries_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exports_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deep_research_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class FeatureSnapshot(Base, TimestampMixin):
    """Leakage-safe pregame features. Rolling stats exclude the current game."""

    __tablename__ = "feature_snapshots"
    __table_args__ = (
        UniqueConstraint("game_id", "feature_version", name="uq_feature_snapshots_game_ver"),
        Index("ix_feature_snapshots_season", "season", "week"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(32), ForeignKey("games.game_id"), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prediction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    known_at_max: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    era: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    home_team: Mapped[str] = mapped_column(String(8), nullable=False)
    away_team: Mapped[str] = mapped_column(String(8), nullable=False)
    home_rest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_rest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rest_diff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elo_home: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elo_away: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elo_diff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elo_win_home: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    srs_home: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    srs_away: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    srs_diff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    srs_pred_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hfa_prior: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adj_off_home: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adj_def_home: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adj_off_away: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adj_def_away: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    adj_pred_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_off_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_off_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_def_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_def_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_pass_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_pass_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_rush_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_rush_epa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_pass_epa_allowed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_pass_epa_allowed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_rush_epa_allowed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_rush_epa_allowed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    success_rate_diff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    explosive_play_diff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_win: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_spread: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extras_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ModelPrediction(Base, TimestampMixin):
    """Model output logged per game (Phase 3+)."""

    __tablename__ = "model_predictions"
    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "model_name",
            "model_version",
            name="uq_model_predictions",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("games.game_id"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    home_win_prob: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_spread: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_home_win_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    edge: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    features_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
