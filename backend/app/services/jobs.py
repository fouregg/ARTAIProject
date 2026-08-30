"""Реестр фоновых задач генерации.

Генерация занимает 30–90 с, а туннели рвут HTTP-запрос примерно на 100 с, поэтому
POST /api/generate сразу отдаёт job_id, а фронт опрашивает GET /api/jobs/{id}.
Реестр живёт в памяти процесса — uvicorn запускается в один воркер.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.schemas import GenerationPayload, JobStage

JOB_TTL_SECONDS = 30 * 60


@dataclass
class Job:
    id: str
    status: Literal["pending", "running", "done", "error"] = "pending"
    stage: JobStage = "queued"
    generation: GenerationPayload | None = None
    error: str | None = None
    error_code: str | None = None
    created_at: float = field(default_factory=time.monotonic)


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self) -> Job:
        self._evict_expired()
        job = Job(id=uuid.uuid4().hex)
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def mark_running(self, job: Job, stage: JobStage) -> None:
        job.status = "running"
        job.stage = stage

    def mark_done(self, job: Job, generation: GenerationPayload) -> None:
        job.status = "done"
        job.stage = "done"
        job.generation = generation

    def mark_error(self, job: Job, message: str, code: str | None = None) -> None:
        job.status = "error"
        job.stage = "error"
        job.error = message
        job.error_code = code

    def _evict_expired(self) -> None:
        deadline = time.monotonic() - JOB_TTL_SECONDS
        for job_id in [j.id for j in self._jobs.values() if j.created_at < deadline]:
            self._jobs.pop(job_id, None)


registry = JobRegistry()
