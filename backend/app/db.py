from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/codementorai"


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    if database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return database_url


def create_session_factory(
    database_url: str,
    *,
    echo: bool = False,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    created_engine = create_async_engine(normalize_database_url(database_url), echo=echo)
    session_factory = async_sessionmaker(created_engine, expire_on_commit=False)
    return created_engine, session_factory


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

engine, AsyncSessionFactory = create_session_factory(DATABASE_URL, echo=SQL_ECHO)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session
