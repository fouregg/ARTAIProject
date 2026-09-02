from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.api.dependencies import require_access_email
from app.models import DomeItem, Generation, GalleryItem, User
from app.schemas import GalleryAddRequest, GalleryItemOut
from app.services.cleanup import EXPIRED_DETAIL

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


def _to_out(item: GalleryItem, generation: Generation, on_canvas: bool = False) -> GalleryItemOut:
    return GalleryItemOut(
        id=item.id,
        on_canvas=on_canvas,
        generation_id=generation.id,
        url=f"/api/images/{generation.id}/file",
        thumb_url=f"/api/images/{generation.id}/thumb",
        title=item.title,
        prompt_original=generation.prompt_original,
        prompt_translated=generation.prompt_translated,
        detected_lang=generation.detected_lang,
        created_at=item.created_at,
    )


@router.post("", response_model=GalleryItemOut, status_code=status.HTTP_201_CREATED)
async def add_to_gallery(
    payload: GalleryAddRequest,
    user: User = Depends(require_access_email),
    session: AsyncSession = Depends(get_session),
) -> GalleryItemOut:
    generation = await session.get(Generation, payload.generation_id)
    # Чужую генерацию сохранять нельзя. Кроме приватности тут есть и практическая
    # причина: generation_id уникален в gallery_items, и первый сохранивший занял бы
    # чужую картинку так, что владелец уже не смог бы добавить её себе.
    if generation is None or generation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Изображение не найдено.")
    if generation.status != "done" or not generation.file_path:
        raise HTTPException(status.HTTP_410_GONE, detail=EXPIRED_DETAIL)

    existing = await session.scalar(
        select(GalleryItem).where(
            GalleryItem.generation_id == generation.id,
            GalleryItem.user_id == user.id,
        )
    )
    if existing is not None:
        # Картинка уже в галерее автоматически — нажатие кнопки делает её постоянной.
        if existing.is_auto:
            existing.is_auto = False
            existing.title = payload.title or existing.title
            await session.commit()
            await session.refresh(existing)
        return _to_out(existing, generation)

    item = GalleryItem(generation_id=generation.id, user_id=user.id, title=payload.title)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return _to_out(item, generation)


@router.get("", response_model=list[GalleryItemOut])
async def list_gallery(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_access_email),
    session: AsyncSession = Depends(get_session),
) -> list[GalleryItemOut]:
    """Галерея личная: гость видит только то, что сохранил сам."""
    on_canvas = exists().where(
        DomeItem.generation_id == Generation.id,
        DomeItem.is_visible.is_(True),
    )
    rows = await session.execute(
        select(GalleryItem, Generation, on_canvas)
        .join(Generation, GalleryItem.generation_id == Generation.id)
        .where(GalleryItem.user_id == user.id)
        .order_by(GalleryItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_to_out(item, generation, shown) for item, generation, shown in rows.all()]


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gallery_item(
    item_id: int,
    user: User = Depends(require_access_email),
    session: AsyncSession = Depends(get_session),
) -> None:
    item = await session.get(GalleryItem, item_id)
    # Чужую запись не показываем и не выдаём её существование: тот же 404.
    if item is None or item.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Элемент галереи не найден.")

    # Файл не трогаем: генерация может висеть на куполе, а если нет —
    # её подберёт уборщик, когда истечёт срок хранения.
    await session.delete(item)
    await session.commit()
