import asyncio
import logging
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import PROJECT_ROOT, get_settings
from app.db import SessionLocal, engine
from app.routers import auth, dome, gallery, generate, health, legal
from app.services.cleanup import worker as cleanup_worker
from app.services.dome_hub import hub
from app.services.generation import get_default_user
from app.services.provod import ProvodClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[1]

# В slim-образе нет /etc/mime.types, и шрифты уезжают как text/plain.
# Регистрируем то, что отдаём сами.
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    # Не даём alembic перенастроить логирование под собой — см. alembic/env.py.
    config.attributes["configure_logger"] = False
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)

    if not settings.provod_api_key:
        logger.warning("PROVOD_API_KEY пуст — генерация работать не будет. Заполните .env")

    if settings.auto_migrate:
        try:
            await asyncio.to_thread(_run_migrations)
            logger.info("Миграции применены")
        except Exception:
            logger.exception(
                "Не удалось применить миграции. Поднят ли PostgreSQL "
                "(docker compose up -d) и верен ли DATABASE_URL?"
            )

    app.state.http = httpx.AsyncClient(
        base_url=settings.provod_base_url,
        headers={
            "Authorization": f"Bearer {settings.provod_api_key}",
            "Content-Type": "application/json",
        },
    )
    app.state.provod = ProvodClient(app.state.http)

    try:
        async with SessionLocal() as session:
            await get_default_user(session)
    except Exception:
        logger.exception("Не удалось создать служебного пользователя")

    hub.start_ping_loop()
    cleanup_worker.start()
    logger.info(
        "Незакреплённые изображения удаляются через %s мин, проверка каждые %s мин",
        settings.image_ttl_minutes,
        settings.cleanup_interval_minutes,
    )
    try:
        yield
    finally:
        await cleanup_worker.stop()
        await hub.stop_ping_loop()
        await app.state.http.aclose()
        await engine.dispose()


app = FastAPI(title="ARTAI — купольный генератор изображений", lifespan=lifespan)

# Логотипы в SVG и бандлы фронта сжимаются вдвое-втрое — заметно на киоске через туннель.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(legal.router)
app.include_router(generate.router)
app.include_router(gallery.router)
app.include_router(dome.router)

# --- собранный фронтенд (npm run build) отдаётся тем же приложением ---------
# Один origin: у купола не будет ни CORS, ни mixed-content при работе через туннель.
_dist = get_settings().frontend_dist
if (_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "ws/")):
            raise HTTPException(status_code=404)

        candidate = (_dist / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(_dist.resolve()):
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")

else:
    logger.info(
        "Сборки фронтенда нет (%s). В деве запускайте vite отдельно: npm run dev",
        _dist.relative_to(PROJECT_ROOT),
    )
