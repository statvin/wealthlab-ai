"""Modelos ORM (SQLAlchemy 2.0).

Persistem o que a spec pede: carteiras, ativos, configurações e simulações
(com seed, para reprodutibilidade). Entradas de execução variáveis (juros,
fluxo, alvo, meta) e o resultado computado ficam como JSON na simulação —
pragmático para um produto pessoal, sem normalizar demais.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wealthlab_api.database import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String, unique=True, index=True)
    nome: Mapped[str] = mapped_column(String)
    classe: Mapped[str] = mapped_column(String)  # AssetClass.value

    # Termos de renda fixa (nulos para renda variável).
    fi_indexador: Mapped[str | None] = mapped_column(String, nullable=True)
    fi_taxa_contratada: Mapped[float | None] = mapped_column(Float, nullable=True)
    fi_duration_anos: Mapped[float | None] = mapped_column(Float, nullable=True)
    fi_vencimento: Mapped[str | None] = mapped_column(String, nullable=True)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String, default="Carteira")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)

    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    quantidade: Mapped[float] = mapped_column(Float)
    preco_inicial: Mapped[float] = mapped_column(Float, default=1.0)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="holdings")
    asset: Mapped["Asset"] = relationship()


class SimulationConfig(Base):
    __tablename__ = "simulation_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    n_cenarios: Mapped[int] = mapped_column(Integer)
    horizonte_anos: Mapped[float] = mapped_column(Float)
    seed: Mapped[int] = mapped_column(Integer)
    inflacao_aa: Mapped[float] = mapped_column(Float)
    rebalanceamento: Mapped[str] = mapped_column(String)  # RebalanceMode.value
    df_tstudent: Mapped[float] = mapped_column(Float)


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    config_id: Mapped[int] = mapped_column(ForeignKey("simulation_configs.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora)
    status: Mapped[str] = mapped_column(String, default="pendente")

    # Entradas de execução (reprodutibilidade) + resultado computado, como JSON.
    entradas: Mapped[dict] = mapped_column(JSON)     # juros, fluxo, alvo, meta
    resultado: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    portfolio: Mapped["Portfolio"] = relationship()
    config: Mapped["SimulationConfig"] = relationship()
