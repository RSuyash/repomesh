from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import agents, context, events, health, locks, tasks
from app.config.logging import configure_logging
from app.db import create_all
from app.mcp import http
from app.services.errors import AppError

configure_logging()

app = FastAPI(title='RepoMesh API', version='0.1.0')

app.include_router(health.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(locks.router)
app.include_router(events.router)
app.include_router(context.router)
app.include_router(http.router)


@app.on_event('startup')
def on_startup() -> None:
    create_all()


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
