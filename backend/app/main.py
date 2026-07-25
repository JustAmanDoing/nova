import asyncio
import logging
from _thread import RLock
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.services.backup import BackupService
from app.services.intake import IntakeService
from app.services.ocr import LocalOcrService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        operation_lock = RLock()
        ocr_engine = (
            LocalOcrService(
                max_pages=resolved_settings.ocr_max_pages,
                timeout_seconds=resolved_settings.ocr_timeout_seconds,
                max_render_dimension=resolved_settings.ocr_max_render_dimension,
                max_rendered_bytes=resolved_settings.ocr_max_rendered_bytes,
            )
            if resolved_settings.ocr_enabled
            else None
        )
        intake = IntakeService(
            intake_path=resolved_settings.intake_path,
            library_path=resolved_settings.library_path,
            database_path=resolved_settings.database_path,
            max_text_bytes=resolved_settings.max_text_bytes,
            max_extracted_text_bytes=resolved_settings.max_extracted_text_bytes,
            action_stale_seconds=resolved_settings.action_stale_seconds,
            operation_lock=operation_lock,
            ocr_engine=ocr_engine,
        )
        await asyncio.to_thread(intake.initialize)
        await asyncio.to_thread(intake.scan)

        def reconcile_restored_database() -> None:
            intake.initialize()
            intake.scan()

        backups = BackupService(
            database_path=resolved_settings.database_path,
            backup_path=resolved_settings.backup_path,
            operation_lock=operation_lock,
            post_restore=reconcile_restored_database,
        )
        await asyncio.to_thread(backups.initialize)
        application.state.intake = intake
        application.state.backups = backups
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
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=resolved_settings.allowed_hosts,
    )

    @application.middleware("http")
    async def prevent_api_caching(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        if request.url.path.startswith(resolved_settings.api_prefix):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response

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
