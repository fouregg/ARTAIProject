"""Уборщик просроченных изображений.

Сгенерированная картинка лежит на диске ограниченное время. Её сохраняет от удаления
любое явное действие пользователя: отправка на купол или сохранение в галерею.
Всё, что за час никуда не закрепили, считается черновиком и удаляется.

Запись в `generations` остаётся — это журнал, по нему считаются суточные квоты;
у просроченной записи обнуляется `file_path` и статус становится `expired`.
"""

import asyncio
import contextlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import exists, select

from app.config import get_settings
from app.db import SessionLocal
from app.models import DomeItem, GalleryItem, Generation
from app.services import storage

logger = logging.getLogger(__name__)

EXPIRED_DETAIL = (
    "Срок хранения изображения истёк. Незакреплённые картинки удаляются: "
    "сохраните в галерею или отправьте на купол, чтобы оставить навсегда."
)


async def sweep_expired_images() -> int:
    """Удаляет файлы незакреплённых генераций старше TTL. Возвращает число удалённых."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.image_ttl_minutes)

    pinned_to_dome = exists().where(DomeItem.generation_id == Generation.id)
    pinned_to_gallery = exists().where(
        GalleryItem.generation_id == Generation.id,
        GalleryItem.is_auto.is_(False),
    )

    async with SessionLocal() as session:
        expired = (
            await session.scalars(
                select(Generation).where(
                    Generation.file_path.is_not(None),
                    Generation.created_at < cutoff,
                    ~pinned_to_dome,
                    ~pinned_to_gallery,
                )
            )
        ).all()

        for generation in expired:
            if generation.file_path:
                storage.delete_image(generation.file_path)
            generation.file_path = None
            generation.status = "expired"

        if expired:
            await session.commit()

    if expired:
        logger.info("Удалено просроченных изображений: %s", len(expired))
    return len(expired)


class CleanupWorker:
    """Периодическая уборка. Первый проход — сразу на старте, чтобы догнать простой."""

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _loop(self) -> None:
        interval = get_settings().cleanup_interval_minutes * 60
        while True:
            try:
                await sweep_expired_images()
            except Exception:  # noqa: BLE001 — уборка не должна ронять приложение
                logger.exception("Проход уборщика не удался")
            await asyncio.sleep(interval)


worker = CleanupWorker()
