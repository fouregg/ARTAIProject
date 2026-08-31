"""Модерация коллажа.

Пункт 7.1 Соглашения даёт оператору право скрыть отдельный результат генерации,
а пункт 8.3 требует прекратить показ в течение суток по обоснованному обращению.
Снятие с холста — мягкое: запись остаётся, гасится флаг is_visible. Так виден
и сам факт показа, и то, что его прекратили.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_token
from app.api.routes.dome import to_out as dome_item_out
from app.db import get_session
from app.models import DomeItem, Generation
from app.schemas import AdminDomeItemOut
from app.services.dome_hub import hub

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _to_out(item: DomeItem, generation: Generation) -> AdminDomeItemOut:
    return AdminDomeItemOut(
        id=item.id,
        generation_id=generation.id,
        url=f"/api/images/{generation.id}/file",
        prompt_original=generation.prompt_original,
        prompt_translated=generation.prompt_translated,
        detected_lang=generation.detected_lang,
        is_visible=item.is_visible,
        position=item.position,
        created_at=item.created_at,
    )


async def _get_pair(session: AsyncSession, item_id: int) -> tuple[DomeItem, Generation]:
    row = (
        await session.execute(
            select(DomeItem, Generation)
            .join(Generation, DomeItem.generation_id == Generation.id)
            .where(DomeItem.id == item_id)
        )
    ).first()

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Плитка не найдена.")
    return row[0], row[1]


@router.get("/dome", response_model=list[AdminDomeItemOut])
async def list_dome_items(
    _: str = Depends(require_admin_token),
    session: AsyncSession = Depends(get_session),
) -> list[AdminDomeItemOut]:
    """Всё, что когда-либо отправляли на холст, включая уже скрытое."""
    rows = await session.execute(
        select(DomeItem, Generation)
        .join(Generation, DomeItem.generation_id == Generation.id)
        .order_by(DomeItem.position.desc())
    )
    return [_to_out(item, generation) for item, generation in rows.all()]


@router.delete("/dome/{item_id}", response_model=AdminDomeItemOut)
async def hide_dome_item(
    item_id: int,
    _: str = Depends(require_admin_token),
    session: AsyncSession = Depends(get_session),
) -> AdminDomeItemOut:
    item, generation = await _get_pair(session, item_id)

    if item.is_visible:
        item.is_visible = False
        await session.commit()
        await session.refresh(item)
        await hub.broadcast({"type": "image_removed", "id": item.id})

    return _to_out(item, generation)


@router.post("/dome/{item_id}/restore", response_model=AdminDomeItemOut)
async def restore_dome_item(
    item_id: int,
    _: str = Depends(require_admin_token),
    session: AsyncSession = Depends(get_session),
) -> AdminDomeItemOut:
    """Обратная кнопка: на живой инсталляции промахнуться легко."""
    item, generation = await _get_pair(session, item_id)

    if not item.is_visible:
        item.is_visible = True
        await session.commit()
        await session.refresh(item)
        out = dome_item_out(item, generation)
        await hub.broadcast({"type": "image_added", "item": out.model_dump(mode="json")})

    return _to_out(item, generation)


@router.delete("/dome", status_code=status.HTTP_204_NO_CONTENT)
async def clear_dome(
    _: str = Depends(require_admin_token),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Очистить холст целиком. Записи остаются — гасятся только флаги показа."""
    await session.execute(update(DomeItem).values(is_visible=False))
    await session.commit()
    await hub.broadcast({"type": "cleared"})
