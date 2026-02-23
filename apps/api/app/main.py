from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import adapters, agents, context, events, health, locks, orchestrator, recovery, summarizer, tasks
from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.db import create_all
from app.mcp import http
from app.services.adapter_runtime import adapter_runtime
from app.services.errors import AppError
from app.services.orchestrator_runtime import orchestrator_runtime
from app.services.summarizer_runtime import summarizer_runtime

configure_logging()

app = FastAPI(title='RepoMesh API', version='0.1.0')

app.include_router(health.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(locks.router)
app.include_router(events.router)
app.include_router(context.router)
app.include_router(recovery.router)
app.include_router(orchestrator.router)
app.include_router(adapters.router)
app.include_router(summarizer.router)
app.include_router(http.router)


@app.on_event('startup')
async def on_startup() -> None:
    create_all()
    settings = get_settings()
    if settings.orchestrator_autostart:
        await orchestrator_runtime.start()
    if settings.adapter_autostart:
        await adapter_runtime.start()
    if settings.summarizer_autostart:
        await summarizer_runtime.start()


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await orchestrator_runtime.stop()
    await adapter_runtime.stop()
    await summarizer_runtime.stop()


@app.exception_handler(AppError)
def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.details or {},
            }
        },
    )
