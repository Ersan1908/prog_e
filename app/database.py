"""Подключение SQLite и сессия на время одного HTTP-запроса."""

import os
from collections.abc import Generator
from pathlib import Path

from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'movies.db'}"


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None) -> Engine:
    url = make_url(database_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
    if url.get_backend_name() != "sqlite":
        raise ValueError("Этот учебный проект использует SQLite")
    if url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _record):
        # Встроенный lower() SQLite не меняет регистр кириллицы.
        connection.create_function("casefold", 1, str.casefold, deterministic=True)

    return engine


def get_session(request: Request) -> Generator[Session, None, None]:
    with request.app.state.session_factory() as session:
        yield session
