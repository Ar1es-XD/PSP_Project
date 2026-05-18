from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.system import router as system_router
from app.api.router import api_router
from app.core.config import get_settings
from app.core.db import build_engine, build_session_maker
from app.core.exceptions import add_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import (
    BodySizeLimitMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    ResilienceMiddleware,
)
from app.core.observability import configure_tracing
from app.services.db_validation import ensure_migrations
from app.services.simulation_store import SimulationStore


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await ensure_migrations(app.state.db_engine, settings.alembic_ini_path)
        yield
        await app.state.db_engine.dispose()

    app = FastAPI(title="Password Evolver API", version="1.0.0", lifespan=lifespan)

    app.state.settings = settings
    app.state.db_engine = build_engine(settings)
    app.state.db_sessionmaker = build_session_maker(app.state.db_engine)
    app.state.store = SimulationStore(app.state.db_sessionmaker)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=settings.max_body_bytes)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(ResilienceMiddleware)

    add_exception_handlers(app)
    configure_tracing(app, settings)

    app.include_router(api_router)
    app.include_router(system_router)

    return app


app = create_app()
