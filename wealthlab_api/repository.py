"""Acesso a dados (CRUD). Nada de lógica de negócio aqui."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from wealthlab_api import models, schemas


def get_or_create_asset(db: Session, dto: schemas.AssetDTO) -> models.Asset:
    existente = db.execute(
        select(models.Asset).where(models.Asset.ticker == dto.ticker)
    ).scalar_one_or_none()
    if existente is not None:
        return existente

    termos = dto.fixed_income_terms
    asset = models.Asset(
        ticker=dto.ticker,
        nome=dto.nome,
        classe=dto.classe.value,
        fi_indexador=termos.indexador.value if termos else None,
        fi_taxa_contratada=termos.taxa_contratada if termos else None,
        fi_duration_anos=termos.duration_anos if termos else None,
        fi_vencimento=termos.vencimento if termos else None,
    )
    db.add(asset)
    db.flush()
    return asset


def create_portfolio(db: Session, dto: schemas.PortfolioCreate) -> models.Portfolio:
    portfolio = models.Portfolio(nome=dto.nome)
    for h in dto.holdings:
        asset = get_or_create_asset(db, h.asset)
        portfolio.holdings.append(
            models.Holding(
                asset=asset, quantidade=h.quantidade, preco_inicial=h.preco_inicial
            )
        )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


def get_portfolio(db: Session, portfolio_id: int) -> models.Portfolio | None:
    return db.get(models.Portfolio, portfolio_id)


def create_config(db: Session, dto: schemas.SimulationConfigDTO) -> models.SimulationConfig:
    cfg = models.SimulationConfig(
        n_cenarios=dto.n_cenarios,
        horizonte_anos=dto.horizonte_anos,
        seed=dto.seed,
        inflacao_aa=dto.inflacao_aa,
        rebalanceamento=dto.rebalanceamento.value,
        df_tstudent=dto.df_tstudent,
    )
    db.add(cfg)
    db.flush()
    return cfg


def create_simulation(
    db: Session,
    portfolio_id: int,
    config_id: int,
    entradas: dict,
    resultado: dict | None,
    status: str,
) -> models.Simulation:
    sim = models.Simulation(
        portfolio_id=portfolio_id,
        config_id=config_id,
        entradas=entradas,
        resultado=resultado,
        status=status,
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


def get_simulation(db: Session, simulation_id: int) -> models.Simulation | None:
    return db.get(models.Simulation, simulation_id)
