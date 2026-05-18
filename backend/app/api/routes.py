from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.models.schemas import SimulationCreate, SimulationStatus
from app.services.simulation_store import SimulationStore
from app.services.task_queue import enqueue_simulation, revoke_task

router = APIRouter()


def get_store(request: Request) -> SimulationStore:
    return request.app.state.store


def get_settings_dep() -> Settings:
    return get_settings()


@router.post("/simulations", response_model=SimulationStatus)
async def create_simulation(
    payload: SimulationCreate,
    store: SimulationStore = Depends(get_store),
    settings: Settings = Depends(get_settings_dep),
) -> SimulationStatus:
    if await store.count_active() >= settings.max_active_simulations:
        raise HTTPException(status_code=429, detail="simulation capacity reached")
    if len(payload.target) > settings.max_target_length:
        raise HTTPException(status_code=422, detail="target too long")
    if payload.charset and len(payload.charset) > settings.max_charset_length:
        raise HTTPException(status_code=422, detail="charset too long")
    state = await store.create(payload, default_charset=settings.default_charset, update_every=settings.update_every)
    try:
        task_id = enqueue_simulation(state.id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="queue backlog exceeded")
    await store.update_task_id(state.id, task_id)
    status = await store.get_status(state.id)
    if status is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    return status


@router.get("/simulations/{simulation_id}", response_model=SimulationStatus)
async def get_simulation(
    simulation_id: str,
    store: SimulationStore = Depends(get_store),
) -> SimulationStatus:
    status = await store.get_status(simulation_id)
    if status is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    return status


@router.delete("/simulations/{simulation_id}")
async def stop_simulation(
    simulation_id: str,
    store: SimulationStore = Depends(get_store),
) -> dict:
    simulation = await store.get(simulation_id)
    if simulation is None:
        raise HTTPException(status_code=404, detail="simulation not found")
    if simulation.task_id:
        revoke_task(simulation.task_id)
    await store.mark_status(simulation_id, "canceled")
    return {"status": "stopped"}


