from collections.abc import Callable

from fastapi import FastAPI

from app.config import Settings


def get_fastapi_app(config: Settings, lifespan: Callable) -> FastAPI:
    """Голое приложение без единой зависимости — всё остальное навешивает setup.py."""
    return FastAPI(
        title=config.app_title,
        version=config.app_version,
        lifespan=lifespan,
    )
