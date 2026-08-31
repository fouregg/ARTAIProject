"""Файлы изображений лежат на диске, в БД хранится только относительный путь."""

import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)

MIME_BY_FORMAT = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}

# Оригинал 1024×1024 весит около двух мегабайт. На холсте плитка занимает сотню
# пикселей, и полсотни оригиналов на странице — это сотни мегабайт на загрузку.
# Поэтому рядом с картинкой кладём лёгкое превью и отдаём его в коллаж и галерею.
THUMBNAIL_SIZE = 384
THUMBNAIL_QUALITY = 82
THUMBNAIL_SUFFIX = ".thumb.webp"


def save_image(data: bytes, generation_id: uuid.UUID, output_format: str = "png") -> str:
    """Кладёт байты в storage/<год>/<месяц>/<id>.<ext>, возвращает путь относительно storage."""
    now = datetime.now(timezone.utc)
    relative = Path(f"{now:%Y}") / f"{now:%m}" / f"{generation_id}.{output_format}"

    target = get_settings().storage_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

    _write_thumbnail(target, data)
    return relative.as_posix()


def _thumbnail_path(original: Path) -> Path:
    return original.with_suffix(original.suffix + THUMBNAIL_SUFFIX)


def _write_thumbnail(original: Path, data: bytes | None = None) -> Path | None:
    """Кладёт превью рядом с оригиналом. Не удалось — не беда, отдадим оригинал."""
    try:
        raw = data if data is not None else original.read_bytes()
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        image.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.LANCZOS)

        thumb = _thumbnail_path(original)
        image.save(thumb, "WEBP", quality=THUMBNAIL_QUALITY, method=4)
        return thumb
    except Exception:
        logger.warning("Не удалось сделать превью для %s", original.name, exc_info=True)
        return None


def resolve_thumbnail(relative_path: str) -> Path | None:
    """Путь к превью. Для картинок, сделанных до появления превью, создаёт его на лету."""
    original = resolve_path(relative_path)
    if original is None:
        return None

    thumb = _thumbnail_path(original)
    if thumb.is_file():
        return thumb
    return _write_thumbnail(original)


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
        _thumbnail_path(path).unlink(missing_ok=True)
        path.unlink(missing_ok=True)
