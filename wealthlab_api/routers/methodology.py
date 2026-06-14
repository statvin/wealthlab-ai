"""Endpoint da aba Metodologia."""

from __future__ import annotations

from fastapi import APIRouter

from wealthlab_api.methodology import METHODOLOGY

router = APIRouter(tags=["methodology"])


@router.get("/methodology")
def get_methodology() -> dict:
    return METHODOLOGY
