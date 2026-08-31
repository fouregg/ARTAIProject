import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LanguageChoice = Literal["auto", "ru", "en", "zh", "fr", "es", "pt", "ar"]
AspectRatio = Literal["1:1", "3:2", "2:3"]
Quality = Literal["auto", "low", "medium", "high"]
JobStage = Literal["queued", "checking", "translating", "generating", "done", "error"]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class AccessStateOut(BaseModel):
    email: str
    limit: int
    used: int
    remaining: int
    # Анкета участника заполнена и обе отметки проставлены — можно вводить промпт.
    registered: bool


class AcceptedDocument(BaseModel):
    """Что именно человек видел на экране в момент акцепта (п. 12.1 Соглашения)."""

    key: Literal["agreement", "consent"]
    version: str = Field(max_length=16)
    sha256: str = Field(min_length=64, max_length=64)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    last_name: str = Field(min_length=1, max_length=120)
    first_name: str = Field(min_length=1, max_length=120)
    middle_name: str | None = Field(default=None, max_length=120)
    birth_date: date
    country: str = Field(min_length=1, max_length=120)
    is_legal_representative: bool = False
    accepted: list[AcceptedDocument]
    ui_language: str = Field(default="ru", max_length=8)


class LegalDocumentOut(BaseModel):
    key: str
    title: str
    version: str
    sha256: str
    text: str


class LegalBundleOut(BaseModel):
    documents: list[LegalDocumentOut]
    policy_url: str
    checkbox_agreement: str
    checkbox_consent: str
    age_notice: str
    ai_disclosure: str
    rejection_notice: str


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    lang: LanguageChoice = "auto"
    aspect_ratio: AspectRatio = "1:1"
    quality: Quality = "medium"
    # «Сгенерировать снова» присылает уже переведённый промпт — второй раз не переводим.
    skip_translation: bool = False
    # Текст, который набрал пользователь: с skip_translation в prompt лежит перевод,
    # а в журнал и в интерфейс должен попадать оригинал.
    original_prompt: str | None = Field(default=None, max_length=2000)


class JobCreated(BaseModel):
    job_id: str


class GenerationPayload(BaseModel):
    """То, что уходит на фронт: плоский объект с уже готовым url картинки."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    thumb_url: str
    prompt_original: str
    prompt_translated: str | None
    source_lang: str | None
    detected_lang: str | None
    translation_degraded: bool
    size: str
    quality: str
    created_at: datetime
    # Когда файл будет удалён, если его не отправят на купол и не сохранят в галерею.
    expires_at: datetime


class JobStatus(BaseModel):
    job_id: str
    status: Literal["pending", "running", "done", "error"]
    stage: JobStage
    generation: GenerationPayload | None = None
    error: str | None = None
    error_code: str | None = None


class GalleryAddRequest(BaseModel):
    generation_id: uuid.UUID
    title: str | None = Field(default=None, max_length=255)


class GalleryItemOut(BaseModel):
    id: int
    generation_id: uuid.UUID
    url: str
    thumb_url: str
    title: str | None
    prompt_original: str
    prompt_translated: str | None
    detected_lang: str | None
    created_at: datetime


class DomeDisplayRequest(BaseModel):
    generation_id: uuid.UUID


class DomeItemOut(BaseModel):
    id: int
    generation_id: uuid.UUID
    url: str
    thumb_url: str
    prompt: str
    position: int
    created_at: datetime


class DomePreviewItemOut(BaseModel):
    """Для мини-полотна на терминале нужны только картинки, без текстов запросов."""

    id: int
    thumb_url: str


class DomePreviewOut(BaseModel):
    items: list[DomePreviewItemOut]
    page: int
    page_count: int
    total: int


class AdminDomeItemOut(BaseModel):
    """То же, что видит экран, плюс поля, нужные для модерации."""

    id: int
    generation_id: uuid.UUID
    url: str
    thumb_url: str
    prompt_original: str
    prompt_translated: str | None
    detected_lang: str | None
    is_visible: bool
    position: int
    created_at: datetime


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    database: str
    image_model: str
    image_model_available: bool | None
    provod: str
    dome_clients: int
