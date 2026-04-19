from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.logger.log_handler import get_logger
from src.models import Base
from src.settings import SETTINGS

logger = get_logger(__name__)

engine: AsyncEngine = create_async_engine(
    SETTINGS.DB.URL,
    echo=SETTINGS.DB.ECHO,
    future=True,
)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    logger.info("database initialized")


async def close_database() -> None:
    await engine.dispose()
    logger.info("database connection closed")


async def check_database() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("database health check failed")
        return False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
