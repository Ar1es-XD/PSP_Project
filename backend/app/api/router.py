from fastapi import APIRouter

from app.api.routes import router as simulation_router

api_router = APIRouter()
api_router.include_router(simulation_router)
