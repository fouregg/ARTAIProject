import uvicorn
from fastapi import FastAPI

from app.api.factories import get_fastapi_app
from app.api.lifespan import lifespan
from app.api.setup import bind_routes, setup_frontend, setup_logging, setup_middlewares
from app.config import get_settings


def get_app() -> FastAPI:
    config = get_settings()

    setup_logging(config=config)

    app = get_fastapi_app(config=config, lifespan=lifespan)
    app = setup_middlewares(app=app, config=config)
    app = bind_routes(app=app)
    # Только после роутов: catch-all фронтенда иначе перехватит /api.
    app = setup_frontend(app=app, config=config)

    return app


if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:get_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True,
    )
