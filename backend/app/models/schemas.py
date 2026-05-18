from typing import List, Optional

from pydantic import BaseModel, Field


class SimulationCreate(BaseModel):
    target: str = Field(min_length=1, max_length=256)
    charset: Optional[str] = None
    update_every: Optional[int] = Field(default=None, ge=1, le=10000)


class SimulationStatus(BaseModel):
    id: str
    target: str
    current: str
    attempts: int
    matched: int
    progress: float
    elapsed: float
    speed: float
    completed: bool


class SimulationEvent(BaseModel):
    type: str
    data: SimulationStatus
