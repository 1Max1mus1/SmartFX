import asyncio
import os
from pathlib import Path

import pytest
from sqlalchemy import delete

TEST_DB_PATH = Path(__file__).resolve().parent.parent / f"test_suite_{os.getpid()}.db"

os.environ.setdefault("DB_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("RATE_PROVIDER", "mock")
os.environ.setdefault("AI_PROVIDER", "mock")

from src.models import Base
from src.services.db import engine


async def _ensure_database_schema() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def _clear_database_rows() -> None:
    async with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            await connection.execute(delete(table))


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    asyncio.run(_ensure_database_schema())
    yield
    asyncio.run(engine.dispose())
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def reset_database():
    asyncio.run(_clear_database_rows())
    yield
