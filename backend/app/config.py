from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .../ARTAIProject/backend/app/config.py -> .../ARTAIProject
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Языки, которые принимает форма ввода. "auto" — определить автоматически.
SUPPORTED_LANGUAGES = ("ru", "en", "zh", "fr", "es", "pt", "ar")

# Пресеты размера, прошедшие ограничения gpt-image-2:
# сторона кратна 16, 655_360 <= w*h <= 8_294_400, max ребро 3840.
ASPECT_PRESETS = {
    "1:1": "1024x1024",
    "3:2": "1536x1024",
    "2:3": "1024x1536",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provod_api_key: str = ""
    provod_base_url: str = "https://api.provod.ai/v1"
    provod_image_model: str = "openai/gpt-image-2"
    provod_text_model: str = "google/gemini-3.1-flash-lite"

    database_url: str = "postgresql+asyncpg://artai:artai@localhost:5433/artai"

    dome_token: str = "change-me"

    # Идентификатор киоска: попадает в запись акцепта (п. 12.1 Соглашения).
    terminal_id: str = "terminal-1"

    storage_dir: str = "storage"
    # Сколько генераций даёт один 5-значный код доступа.
    code_generations_limit: int = 10
    # Незакреплённая картинка (не на куполе и не в галерее) живёт на диске столько минут.
    image_ttl_minutes: int = 60
    cleanup_interval_minutes: int = 10
    auto_migrate: bool = True
    # Список через запятую: pydantic-settings иначе пытается разобрать значение как JSON.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def storage_path(self) -> Path:
        path = Path(self.storage_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def frontend_dist(self) -> Path:
        return PROJECT_ROOT / "frontend" / "dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
