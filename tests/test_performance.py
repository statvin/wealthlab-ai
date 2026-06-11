"""Teste de performance: o critério de aceite da Fase 1.

10.000 cenários × 30 anos × passo mensal devem rodar em poucos segundos.
O limite é folgado para não dar falso-negativo em máquinas/CI mais lentos; o
tempo real é impresso para acompanhamento.
"""

from __future__ import annotations

import time

import numpy as np

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    CashFlowPlan,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
    RebalanceMode,
    SimulationConfig,
    TargetAllocation,
)
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.simulator import simular_portfolio


def _params_quatro_rv() -> EstimatedParams:
    sigma = np.array([0.05, 0.06, 0.07, 0.12])  # mensal; o 4º é "cripto"
    corr = np.array(
        [
            [1.0, 0.5, 0.4, 0.2],
            [0.5, 1.0, 0.3, 0.2],
            [0.4, 0.3, 1.0, 0.1],
            [0.2, 0.2, 0.1, 1.0],
        ]
    )
    cov = np.outer(sigma, sigma) * corr
    mu = np.array([0.008, 0.009, 0.010, 0.015])
    return EstimatedParams(
        tickers=["BR", "INTL", "BR2", "CRYPTO"],
        mu_log_mensal=mu,
        cov_mensal=cov,
        mu_log_aa=mu * 12,
        sigma_aa=sigma * np.sqrt(12),
        corr=corr,
    )


def test_performance_10k_30anos():
    a1 = Asset(ticker="BR", nome="BR", classe=AssetClass.EQUITY_BR)
    a2 = Asset(ticker="INTL", nome="INTL", classe=AssetClass.EQUITY_INTL)
    a3 = Asset(ticker="BR2", nome="BR2", classe=AssetClass.EQUITY_BR)
    cripto = Asset(ticker="CRYPTO", nome="CRYPTO", classe=AssetClass.CRYPTO)
    cdb = Asset(
        ticker="CDB",
        nome="CDB",
        classe=AssetClass.FIXED_INCOME_POS,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=1.0),
    )
    pf = Portfolio(
        holdings=[
            Holding(asset=a1, quantidade=100.0),
            Holding(asset=a2, quantidade=100.0),
            Holding(asset=a3, quantidade=100.0),
            Holding(asset=cripto, quantidade=10.0),
            Holding(asset=cdb, quantidade=10000.0),
        ]
    )
    target = TargetAllocation(
        por_classe={
            AssetClass.EQUITY_BR: 0.45,
            AssetClass.EQUITY_INTL: 0.25,
            AssetClass.CRYPTO: 0.05,
            AssetClass.FIXED_INCOME_POS: 0.25,
        }
    )
    cfg = SimulationConfig(
        n_cenarios=10_000,
        horizonte_anos=30.0,
        seed=1,
        inflacao_aa=0.04,
        rebalanceamento=RebalanceMode.ANUAL_AO_ALVO,
        df_tstudent=6.0,
    )
    cash = CashFlowPlan(aporte_mensal=1000.0)

    t0 = time.perf_counter()
    res = simular_portfolio(
        pf,
        cfg,
        PremissasJuros(selic_aa=0.10, ipca_aa=0.04),
        params_rv=_params_quatro_rv(),
        cashflow=cash,
        target=target,
    )
    dt = time.perf_counter() - t0
    print(f"\n[perf] 10k × 30a × mensal × 5 ativos: {dt:.2f}s")

    assert res.trajetorias_nominais.shape == (10_000, 360 + 1)
    assert dt < 10.0  # "poucos segundos" — limite folgado p/ evitar flakiness
