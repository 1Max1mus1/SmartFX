import asyncio

import pytest

from src.models import Base
from src.services.db import engine


async def _reset_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def reset_database():
    asyncio.run(_reset_database())
    yield

