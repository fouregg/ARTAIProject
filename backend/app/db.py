from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

BACKEND_DIR = Path(__file__).resolve().parents[1]

engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-зависимость: сессия на запрос, коммит вызывает сам роутер."""
    async with SessionLocal() as session:
        yield session


def run_migrations() -> None:
    """Синхронный alembic upgrade head — вызывается из lifespan в отдельном потоке."""
    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    # Не даём alembic перенастроить логирование под собой — см. alembic/env.py.
    config.attributes["configure_logger"] = False
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    command.upgrade(config, "head")
