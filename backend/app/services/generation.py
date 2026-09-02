"""Конвейер генерации: перевод -> gpt-image-2 -> файл на диске -> запись в БД."""

import logging
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ASPECT_PRESETS, get_settings
from app.db import SessionLocal
from app.models import GalleryItem, Generation, User
from app.schemas import GenerateRequest, GenerationPayload
from app.services import storage
from app.services.legal import REJECTION_NOTICE
from app.services.jobs import Job, registry
from app.services.moderation import moderate
from app.services.provod import ProvodClient, ProvodError

logger = logging.getLogger(__name__)

DEFAULT_USER_NAME = "default"


async def get_default_user(session: AsyncSession) -> User:
    """Служебная учётка без кода: к ней привязаны генерации до появления авторизации."""
    user = await session.scalar(select(User).where(User.display_name == DEFAULT_USER_NAME))
    if user is None:
        user = User(
            display_name=DEFAULT_USER_NAME,
            generations_limit=0,
            is_active=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


def to_payload(generation: Generation) -> GenerationPayload:
    ttl = timedelta(minutes=get_settings().image_ttl_minutes)
    return GenerationPayload(
        id=generation.id,
        url=f"/api/images/{generation.id}/file",
        thumb_url=f"/api/images/{generation.id}/thumb",
        prompt_original=generation.prompt_original,
        prompt_translated=generation.prompt_translated,
        source_lang=generation.source_lang,
        detected_lang=generation.detected_lang,
        translation_degraded=generation.translation_degraded,
        size=generation.size,
        quality=generation.quality,
        created_at=generation.created_at,
        expires_at=generation.created_at + ttl,
    )


async def run_generation_job(
    job: Job,
    request: GenerateRequest,
    client: ProvodClient,
    user_id: int,
) -> None:
    """Фоновая задача. Живёт вне запроса, поэтому берёт собственную сессию БД."""
    settings = get_settings()
    size = ASPECT_PRESETS[request.aspect_ratio]
    generation_id = uuid.uuid4()

    async with SessionLocal() as session:
        generation = Generation(
            id=generation_id,
            user_id=user_id,
            prompt_original=request.original_prompt or request.prompt,
            source_lang=None if request.lang == "auto" else request.lang,
            model=settings.provod_image_model,
            size=size,
            quality=request.quality,
            output_format="png",
            status="running",
        )
        session.add(generation)
        await session.commit()

        try:
            # Проверка идёт первой и по исходному тексту: перевод мог бы смягчить
            # формулировку, а платить за генерацию отклонённого запроса незачем.
            registry.mark_running(job, "checking")
            verdict = await moderate(client, request.prompt)
            if not verdict.allowed:
                generation.moderation_categories = verdict.summary or "unavailable"
                await _fail(session, generation, job, REJECTION_NOTICE, "MODERATION_BLOCKED")
                return

            if request.skip_translation:
                # «Сгенерировать снова»: промпт уже английский, второй раз не переводим.
                prompt_en = request.prompt
                generation.prompt_translated = request.prompt
                generation.detected_lang = None if request.lang == "auto" else request.lang
            else:
                registry.mark_running(job, "translating")
                lang = None if request.lang == "auto" else request.lang
                translation = await client.translate(request.prompt, lang)
                prompt_en = translation.prompt_en
                generation.prompt_translated = translation.prompt_en
                generation.detected_lang = translation.detected_lang
                generation.translation_degraded = translation.degraded

            await session.commit()

            registry.mark_running(job, "generating")
            image_bytes = await client.generate_image(
                prompt_en,
                size=size,
                quality=request.quality,
                output_format="png",
            )

            generation.file_path = storage.save_image(image_bytes, generation_id, "png")
            generation.status = "done"

            # Кладём в галерею сразу: иначе обновление страницы теряет работу.
            # is_auto=True — такая запись не удерживает файл от уборки, срок хранения
            # продолжает действовать, пока гость не сохранит картинку сам.
            session.add(GalleryItem(generation_id=generation.id, user_id=user_id, is_auto=True))
            await session.commit()
            await session.refresh(generation)

            registry.mark_done(job, to_payload(generation))
            logger.info("Генерация %s завершена (%s байт)", generation_id, len(image_bytes))

        except ProvodError as exc:
            await _fail(session, generation, job, exc.message, exc.code)
        except Exception:  # noqa: BLE001 — фоновая задача не должна падать молча
            logger.exception("Генерация %s упала", generation_id)
            await _fail(
                session,
                generation,
                job,
                "Внутренняя ошибка при генерации изображения.",
                "INTERNAL_ERROR",
            )


async def _fail(
    session: AsyncSession,
    generation: Generation,
    job: Job,
    message: str,
    code: str | None,
) -> None:
    generation.status = "error"
    generation.error = message
    await session.commit()
    registry.mark_error(job, message, code)
