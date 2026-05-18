from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.registry import SimulationRegistry
from app.services.simulation_engine import SimulationEngine
from app.services.metrics_service import MetricsService
from app.websocket.manager import WebSocketManager


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Password Evolver API", version="1.0.0")

    app.state.settings = settings
    app.state.registry = SimulationRegistry()
    app.state.metrics = MetricsService()
    app.state.websocket_manager = WebSocketManager()
    app.state.engine = SimulationEngine(
        registry=app.state.registry,
        metrics=app.state.metrics,
        websocket_manager=app.state.websocket_manager,
        default_charset=settings.default_charset,
        update_every=settings.update_every,
        step_delay=settings.step_delay,
    )

    app.include_router(api_router)

    return app


app = create_app()
