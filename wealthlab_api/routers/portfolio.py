"""Endpoints de carteira."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from wealthlab_core.domain.enums import AssetClass
from wealthlab_api import models, repository, schemas, services
from wealthlab_api.database import get_db

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _to_out(orm: models.Portfolio) -> schemas.PortfolioOut:
    return schemas.PortfolioOut(
        id=orm.id,
        nome=orm.nome,
        holdings=[
            schemas.HoldingOut(
                ticker=h.asset.ticker,
                nome=h.asset.nome,
                classe=AssetClass(h.asset.classe),
                quantidade=h.quantidade,
                preco_inicial=h.preco_inicial,
            )
            for h in orm.holdings
        ],
    )


@router.post("", response_model=schemas.PortfolioOut, status_code=201)
def criar_portfolio(dto: schemas.PortfolioCreate, db: Session = Depends(get_db)):
    orm = services.criar_carteira(db, dto)
    return _to_out(orm)


@router.get("/{portfolio_id}", response_model=schemas.PortfolioOut)
def obter_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    orm = repository.get_portfolio(db, portfolio_id)
    if orm is None:
        raise HTTPException(status_code=404, detail=f"carteira {portfolio_id} não encontrada.")
    return _to_out(orm)
