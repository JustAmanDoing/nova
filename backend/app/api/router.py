from fastapi import APIRouter

from app.api.routes.backup import router as backup_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.intake import router as intake_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.librarian import router as librarian_router
from app.api.routes.next_actions import router as next_actions_router
from app.api.routes.project_archive import router as project_archive_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(librarian_router)
api_router.include_router(next_actions_router)
api_router.include_router(project_archive_router)
api_router.include_router(backup_router)
api_router.include_router(intake_router)
