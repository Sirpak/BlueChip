"""Database engine and session factory."""

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    url = settings.database_url

    # Ensure parent dir exists for SQLite file URLs
    if url.startswith("sqlite:///"):
        db_path = Path(url.removeprefix("sqlite:///"))
        if not db_path.is_absolute():
            db_path = (get_settings().data_dir.parent / db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{db_path.as_posix()}"

    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        connect_args["timeout"] = 60

    engine = create_engine(url, future=True, connect_args=connect_args)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _sqlite_pragma(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_session() -> Iterator[Session]:
    """Yield a short-lived session (FastAPI dependency style)."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_db_state() -> None:
    """Clear cached engine/session (tests)."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
