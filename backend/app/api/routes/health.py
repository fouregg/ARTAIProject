from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.api.dependencies import get_provod
from app.schemas import HealthOut
from app.services.dome_hub import hub
from app.services.provod import ProvodClient

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health(
    session: AsyncSession = Depends(get_session),
    provod: ProvodClient = Depends(get_provod),
) -> HealthOut:
    settings = get_settings()

    try:
        await session.execute(text("SELECT 1"))
        database = "ok"
    except Exception as exc:  # noqa: BLE001 — health не должен падать
        database = f"error: {exc.__class__.__name__}"

    available = await provod.image_model_available()
    if available is None:
        provod_status = "unreachable"
    elif available:
        provod_status = "ok"
    else:
        provod_status = "model_unavailable"

    overall = "ok" if database == "ok" and available else "degraded"

    return HealthOut(
        status=overall,
        database=database,
        image_model=settings.provod_image_model,
        image_model_available=available,
        provod=provod_status,
        dome_clients=hub.client_count,
    )
