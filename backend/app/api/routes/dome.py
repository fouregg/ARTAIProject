import logging
import math
import secrets
import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, get_session
from app.api.dependencies import require_access_email
from app.models import DomeItem, Generation, User
from app.schemas import DomeDisplayRequest, DomeItemOut, DomePreviewItemOut, DomePreviewOut
from app.services.cleanup import EXPIRED_DETAIL
from app.services.dome_hub import hub

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dome"])

# Холст листает страницы по 50 штук раз в минуту. Обе стороны — экран и мини-полотно
# на терминале — считают номер страницы от одних и тех же часов, иначе миниатюра
# показывала бы не то, что сейчас висит на стене.
PAGE_SIZE = 50
PAGE_INTERVAL_SECONDS = 60


def current_page(page_count: int, now: float | None = None) -> int:
    """Номер текущей страницы, отсчитанный от времени. Нумерация с нуля."""
    if page_count <= 1:
        return 0
    seconds = time.time() if now is None else now
    return int(seconds // PAGE_INTERVAL_SECONDS) % page_count


def require_dome_token(token: str = Query(default="")) -> str:
    """Экран купола висит в интернете — без токена его содержимое не отдаём."""
    expected = get_settings().dome_token
    if not secrets.compare_digest(token, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Неверный токен экрана.")
    return token


def to_out(item: DomeItem, generation: Generation) -> DomeItemOut:
    return DomeItemOut(
        id=item.id,
        generation_id=generation.id,
        url=f"/api/images/{generation.id}/file",
        thumb_url=f"/api/images/{generation.id}/thumb",
        prompt=generation.prompt_translated or generation.prompt_original,
        position=item.position,
        created_at=item.created_at,
    )


async def _load_items(session: AsyncSession) -> list[DomeItemOut]:
    rows = await session.execute(
        select(DomeItem, Generation)
        .join(Generation, DomeItem.generation_id == Generation.id)
        .where(DomeItem.is_visible.is_(True))
        .order_by(DomeItem.position.asc())
    )
    return [to_out(item, generation) for item, generation in rows.all()]


@router.post("/api/dome/display", response_model=DomeItemOut, status_code=status.HTTP_201_CREATED)
async def display_on_dome(
    payload: DomeDisplayRequest,
    _: User = Depends(require_access_email),
    session: AsyncSession = Depends(get_session),
) -> DomeItemOut:
    generation = await session.get(Generation, payload.generation_id)
    if generation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Изображение не найдено.")
    if generation.status != "done" or not generation.file_path:
        raise HTTPException(status.HTTP_410_GONE, detail=EXPIRED_DETAIL)

    max_position = await session.scalar(select(func.max(DomeItem.position)))
    next_position = (max_position or 0) + 1
    item = DomeItem(generation_id=generation.id, position=next_position, is_visible=True)
    session.add(item)
    await session.commit()
    await session.refresh(item)

    out = to_out(item, generation)
    await hub.broadcast({"type": "image_added", "item": out.model_dump(mode="json")})
    return out


@router.get("/api/dome/preview", response_model=DomePreviewOut)
async def dome_preview(session: AsyncSession = Depends(get_session)) -> DomePreviewOut:
    """Что сейчас на холсте — для мини-полотна на экране терминала.

    Без токена: содержимое холста и так висит на стене у всех на виду. Отдаём только
    картинки текущей страницы, без текстов запросов и без полного списка на тысячи строк.
    """
    total = await session.scalar(
        select(func.count(DomeItem.id)).where(DomeItem.is_visible.is_(True))
    ) or 0
    page_count = max(1, math.ceil(total / PAGE_SIZE))
    page = current_page(page_count)

    rows = await session.execute(
        select(DomeItem.id, Generation.id)
        .join(Generation, DomeItem.generation_id == Generation.id)
        .where(DomeItem.is_visible.is_(True))
        .order_by(DomeItem.position.asc())
        .offset(page * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )

    return DomePreviewOut(
        items=[
            DomePreviewItemOut(id=item_id, thumb_url=f"/api/images/{generation_id}/thumb")
            for item_id, generation_id in rows.all()
        ],
        page=page + 1,
        page_count=page_count,
        total=total,
    )


@router.get("/api/dome/items", response_model=list[DomeItemOut])
async def list_dome_items(
    _: str = Depends(require_dome_token),
    session: AsyncSession = Depends(get_session),
) -> list[DomeItemOut]:
    return await _load_items(session)


@router.websocket("/ws/dome")
async def dome_socket(websocket: WebSocket, token: str = Query(default="")) -> None:
    if not secrets.compare_digest(token, get_settings().dome_token):
        await websocket.close(code=4401)
        return

    await hub.connect(websocket)
    try:
        async with SessionLocal() as session:
            items = await _load_items(session)
        await websocket.send_json(
            {"type": "snapshot", "items": [item.model_dump(mode="json") for item in items]}
        )

        # Купол ничего осмысленного не присылает; читаем, чтобы поймать разрыв.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001 — разрыв туннеля не должен светиться трейсбеком
        logger.info("Соединение с куполом закрыто с ошибкой")
    finally:
        await hub.disconnect(websocket)
