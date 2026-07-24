import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.services.intake import IntakeService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        intake = IntakeService(
            intake_path=resolved_settings.intake_path,
            database_path=resolved_settings.database_path,
            max_text_bytes=resolved_settings.max_text_bytes,
            max_extracted_text_bytes=resolved_settings.max_extracted_text_bytes,
        )
        await asyncio.to_thread(intake.initialize)
        await asyncio.to_thread(intake.scan)
        application.state.intake = intake
        watcher = asyncio.create_task(
            watch_intake(intake, resolved_settings.intake_scan_seconds)
        )
        try:
            yield
        finally:
            watcher.cancel()
            with suppress(asyncio.CancelledError):
                await watcher

    application = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        description="Local-first API for Nova's safe file-intake workflow.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    application.state.settings = resolved_settings
    application.include_router(api_router, prefix=resolved_settings.api_prefix)
    return application


async def watch_intake(service: IntakeService, interval_seconds: float) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(service.scan)
        except Exception:
            logger.exception("Background intake scan failed; monitoring will continue.")


app = create_app()
