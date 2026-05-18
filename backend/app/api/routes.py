from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket

from app.models.schemas import SimulationCreate, SimulationStatus
from app.services.registry import SimulationRegistry
from app.services.simulation_engine import SimulationEngine
from app.websocket.manager import WebSocketManager

router = APIRouter()


def get_registry(request: Request) -> SimulationRegistry:
    return request.app.state.registry


def get_engine(request: Request) -> SimulationEngine:
    return request.app.state.engine


def get_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.websocket_manager


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/simulations", response_model=SimulationStatus)
async def create_simulation(
    payload: SimulationCreate,
    registry: SimulationRegistry = Depends(get_registry),
    engine: SimulationEngine = Depends(get_engine),
) -> SimulationStatus:
    state = registry.create(payload)
    await engine.start(state.id)
    return engine.get_status(state.id)


@router.get("/simulations/{simulation_id}", response_model=SimulationStatus)
async def get_simulation(
    simulation_id: str,
    engine: SimulationEngine = Depends(get_engine),
) -> SimulationStatus:
    status = engine.get_status(simulation_id)
    if status is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    return status


@router.delete("/simulations/{simulation_id}")
async def stop_simulation(
    simulation_id: str,
    engine: SimulationEngine = Depends(get_engine),
) -> dict:
    stopped = await engine.stop(simulation_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="simulation not found")
    return {"status": "stopped"}


@router.websocket("/ws/simulations/{simulation_id}")
async def simulation_ws(
    websocket: WebSocket,
    simulation_id: str,
    ws_manager: WebSocketManager = Depends(get_ws_manager),
    engine: SimulationEngine = Depends(get_engine),
) -> None:
    await ws_manager.connect(simulation_id, websocket)
    try:
        status = engine.get_status(simulation_id)
        if status is not None:
            await ws_manager.send_to(simulation_id, status.model_dump())
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        await ws_manager.disconnect(simulation_id, websocket)
