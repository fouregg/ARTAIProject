"""Всё, что навешивается на приложение: логи, middleware, роуты, статика.

main.py только вызывает эти функции по порядку и ничего не знает о деталях.
"""

import logging
import mimetypes

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.auth import router as auth_router
from app.api.routes.dome import router as dome_router
from app.api.routes.gallery import router as gallery_router
from app.api.routes.generate import router as generate_router
from app.api.routes.health import router as health_router
from app.api.routes.legal import router as legal_router
from app.config import PROJECT_ROOT, Settings

logger = logging.getLogger(__name__)

GZIP_MIN_SIZE = 1024


def setup_logging(config: Settings) -> None:
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    # В slim-образе нет /etc/mime.types, и шрифты уезжают как text/plain.
    # Регистрируем то, что отдаём сами.
    mimetypes.add_type("font/woff2", ".woff2")
    mimetypes.add_type("font/woff", ".woff")
    mimetypes.add_type("image/webp", ".webp")
    mimetypes.add_type("image/svg+xml", ".svg")


def setup_middlewares(app: FastAPI, config: Settings) -> FastAPI:
    # Логотипы в SVG и бандлы фронта сжимаются вдвое-втрое — заметно на киоске через туннель.
    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MIN_SIZE)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


def bind_routes(app: FastAPI) -> FastAPI:
    api_router = APIRouter()

    api_router.include_router(router=health_router)
    api_router.include_router(router=auth_router)
    api_router.include_router(router=legal_router)
    api_router.include_router(router=generate_router)
    api_router.include_router(router=gallery_router)
    # Роутер купола держит и websocket, поэтому префикса у него нет.
    api_router.include_router(router=dome_router)

    app.include_router(api_router)

    return app


def setup_frontend(app: FastAPI, config: Settings) -> FastAPI:
    """Собранный фронтенд отдаётся тем же приложением.

    Один origin: у цифрового холста не будет ни CORS, ни mixed-content через туннель.
    Регистрируется последним — catch-all маршрут перехватывает всё, что не /api и не /ws.
    """
    dist = config.frontend_dist

    if not (dist / "index.html").exists():
        logger.info(
            "Сборки фронтенда нет (%s). В деве запускайте vite отдельно: npm run dev",
            dist.relative_to(PROJECT_ROOT),
        )
        return app

    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "ws/")):
            raise HTTPException(status_code=404)

        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(dist.resolve()):
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")

    return app
