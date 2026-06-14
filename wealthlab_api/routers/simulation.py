"""Endpoints de simulação: run, results, risk-analysis, stress-test."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from wealthlab_core.engine.stress import PRESETS
from wealthlab_api import repository, schemas, services
from wealthlab_api.config import Settings, get_settings
from wealthlab_api.database import get_db
from wealthlab_api.market import get_market_provider

router = APIRouter(prefix="/simulation", tags=["simulation"])


def _get_sim_ou_404(db: Session, sim_id: int):
    sim = repository.get_simulation(db, sim_id)
    if sim is None or sim.resultado is None:
        raise HTTPException(status_code=404, detail=f"simulação {sim_id} não encontrada.")
    return sim


@router.post("/run", response_model=schemas.SimulationRunResponse, status_code=201)
def rodar(
    request: schemas.SimulationRunRequest,
    db: Session = Depends(get_db),
    provider=Depends(get_market_provider),
    settings: Settings = Depends(get_settings),
):
    sim = services.executar_simulacao(db, request, provider, settings)
    return schemas.SimulationRunResponse(
        id=sim.id, status=sim.status, resumo=sim.resultado["resumo"]
    )


@router.get("/{sim_id}/results", response_model=schemas.ResultsOut)
def resultados(sim_id: int, db: Session = Depends(get_db)):
    sim = _get_sim_ou_404(db, sim_id)
    return schemas.ResultsOut(
        id=sim.id, resumo=sim.resultado["resumo"], funil=sim.resultado["funil"]
    )


@router.get("/{sim_id}/risk-analysis", response_model=schemas.RiskAnalysisOut)
def risco(sim_id: int, db: Session = Depends(get_db)):
    sim = _get_sim_ou_404(db, sim_id)
    r = sim.resultado["risco"]
    return schemas.RiskAnalysisOut(
        id=sim.id,
        var_cvar=[schemas.VaRCVaROut(**x) for x in r["var_cvar"]],
        prob_ruina=r["prob_ruina"],
        prob_meta=r["prob_meta"],
        drawdown=r["drawdown"],
        contribuicao=r["contribuicao"],
    )


@router.get("/{sim_id}/stress-test", response_model=schemas.StressOut)
def stress_test(
    sim_id: int,
    presets: str | None = Query(default=None, description="Lista separada por vírgula; default = todos."),
    db: Session = Depends(get_db),
    provider=Depends(get_market_provider),
    settings: Settings = Depends(get_settings),
):
    sim = _get_sim_ou_404(db, sim_id)
    nomes = None
    if presets:
        nomes = [p.strip() for p in presets.split(",")]
        desconhecidos = [n for n in nomes if n not in PRESETS]
        if desconhecidos:
            raise HTTPException(
                status_code=400,
                detail=f"presets desconhecidos: {desconhecidos}. Disponíveis: {list(PRESETS)}.",
            )
    comparacoes = services.rodar_stress(db, sim, provider, settings, nomes)
    return schemas.StressOut(id=sim.id, comparacoes=comparacoes)
