"""Файлы изображений лежат на диске, в БД хранится только относительный путь."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

MIME_BY_FORMAT = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}


def save_image(data: bytes, generation_id: uuid.UUID, output_format: str = "png") -> str:
    """Кладёт байты в storage/<год>/<месяц>/<id>.<ext>, возвращает путь относительно storage."""
    now = datetime.now(timezone.utc)
    relative = Path(f"{now:%Y}") / f"{now:%m}" / f"{generation_id}.{output_format}"

    target = get_settings().storage_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return relative.as_posix()


def resolve_path(relative_path: str) -> Path | None:
    """Абсолютный путь к файлу; None — если файла нет или он вне storage."""
    root = get_settings().storage_path.resolve()
    candidate = (root / relative_path).resolve()

    if not candidate.is_relative_to(root) or not candidate.is_file():
        return None
    return candidate


def media_type(relative_path: str) -> str:
    return MIME_BY_FORMAT.get(Path(relative_path).suffix.lstrip("."), "application/octet-stream")


def delete_image(relative_path: str) -> None:
    path = resolve_path(relative_path)
    if path is not None:
        path.unlink(missing_ok=True)
