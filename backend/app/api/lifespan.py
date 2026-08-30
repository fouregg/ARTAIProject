import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config import get_settings
from app.db import SessionLocal, engine, run_migrations
from app.services.cleanup import worker as cleanup_worker
from app.services.dome_hub import hub
from app.services.generation import get_default_user
from app.services.provod import ProvodClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Что живёт столько же, сколько приложение: http-клиент шлюза и фоновые задачи."""
    settings = get_settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)

    if not settings.provod_api_key:
        logger.warning("PROVOD_API_KEY пуст — генерация работать не будет. Заполните .env")

    if settings.auto_migrate:
        try:
            await asyncio.to_thread(run_migrations)
            logger.info("Миграции применены")
        except Exception:
            logger.exception(
                "Не удалось применить миграции. Поднят ли PostgreSQL "
                "(docker compose up -d) и верен ли DATABASE_URL?"
            )

    app.state.http = httpx.AsyncClient(
        base_url=settings.provod_base_url,
        headers={
            "Authorization": f"Bearer {settings.provod_api_key}",
            "Content-Type": "application/json",
        },
    )
    app.state.provod = ProvodClient(app.state.http)

    try:
        async with SessionLocal() as session:
            await get_default_user(session)
    except Exception:
        logger.exception("Не удалось создать служебного пользователя")

    hub.start_ping_loop()
    cleanup_worker.start()
    logger.info(
        "Незакреплённые изображения удаляются через %s мин, проверка каждые %s мин",
        settings.image_ttl_minutes,
        settings.cleanup_interval_minutes,
    )

    try:
        yield
    finally:
        await cleanup_worker.stop()
        await hub.stop_ping_loop()
        await app.state.http.aclose()
        await engine.dispose()
