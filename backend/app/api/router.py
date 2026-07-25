from fastapi import APIRouter

from app.api.routes.backup import router as backup_router
from app.api.routes.health import router as health_router
from app.api.routes.intake import router as intake_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(backup_router)
api_router.include_router(intake_router)
