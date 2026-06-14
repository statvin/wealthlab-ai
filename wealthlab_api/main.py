"""Aplicação FastAPI — casca fina sobre o motor quantitativo.

Mapeia exceções do domínio/motor para respostas HTTP padronizadas:
  - ValidationError (Pydantic, ex.: carteira inválida) -> 422
  - ValueError (regra do motor, ex.: alvo incompatível) -> 422
  - LookupError (recurso inexistente) -> 404
"""

from __future__ import annotations

import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from wealthlab_api.routers import methodology, portfolio, simulation

app = FastAPI(
    title="WealthLab AI API",
    version="0.1.0",
    description="Casca fina sobre o motor quantitativo (Fase 4).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
def _handle_validation(request: Request, exc: ValidationError):
    # exc.json() é garantidamente serializável (errors() pode conter o ValueError
    # original em `ctx`, que não é JSON-serializável).
    return JSONResponse(status_code=422, content={"detail": json.loads(exc.json(include_url=False))})


@app.exception_handler(ValueError)
def _handle_value_error(request: Request, exc: ValueError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(LookupError)
def _handle_lookup(request: Request, exc: LookupError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(portfolio.router)
app.include_router(simulation.router)
app.include_router(methodology.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
