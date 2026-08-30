import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_provod, require_quota
from app.models import Generation, User
from app.schemas import GenerateRequest, JobCreated, JobStatus
from app.services import storage
from app.services.cleanup import EXPIRED_DETAIL
from app.services.generation import run_generation_job
from app.services.jobs import registry
from app.services.provod import ProvodClient

router = APIRouter(prefix="/api", tags=["generate"])

# Держим ссылки на живые задачи, иначе сборщик мусора может их убить.
_running_tasks: set[asyncio.Task] = set()


@router.post("/generate", response_model=JobCreated, status_code=status.HTTP_202_ACCEPTED)
async def create_generation(
    payload: GenerateRequest,
    user: User = Depends(require_quota),
    provod: ProvodClient = Depends(get_provod),
) -> JobCreated:
    job = registry.create()
    task = asyncio.create_task(run_generation_job(job, payload, provod, user.id))
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)

    return JobCreated(job_id=job.id)


@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str) -> JobStatus:
    job = registry.get(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Задача не найдена или устарела.")

    return JobStatus(
        job_id=job.id,
        status=job.status,
        stage=job.stage,
        generation=job.generation,
        error=job.error,
        error_code=job.error_code,
    )


@router.get("/images/{generation_id}/file")
async def get_image_file(
    generation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    generation = await session.get(Generation, generation_id)
    if generation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Изображение не найдено.")

    if generation.status == "expired" or not generation.file_path:
        raise HTTPException(status.HTTP_410_GONE, detail=EXPIRED_DETAIL)

    path = storage.resolve_path(generation.file_path)
    if path is None:
        raise HTTPException(status.HTTP_410_GONE, detail=EXPIRED_DETAIL)

    return FileResponse(
        path,
        media_type=storage.media_type(generation.file_path),
        # Файл иммутабелен: имя содержит uuid генерации.
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
