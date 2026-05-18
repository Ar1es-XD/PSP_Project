from dataclasses import dataclass
from typing import Dict, Optional, List

from app.models.schemas import SimulationCreate
from app.utils.id import generate_id


@dataclass
class SimulationState:
    id: str
    target: str
    charset: str
    update_every: int
    current: List[str]
    attempts: int = 0
    completed: bool = False
    start_time: float = 0.0
    task_id: Optional[int] = None


class SimulationRegistry:
    def __init__(self) -> None:
        self._states: Dict[str, SimulationState] = {}

    def create(self, payload: SimulationCreate) -> SimulationState:
        state_id = generate_id()
        charset = payload.charset
        state = SimulationState(
            id=state_id,
            target=payload.target,
            charset=charset or "",
            update_every=payload.update_every or 0,
            current=[],
        )
        self._states[state_id] = state
        return state

    def get(self, state_id: str) -> Optional[SimulationState]:
        return self._states.get(state_id)

    def remove(self, state_id: str) -> None:
        self._states.pop(state_id, None)
