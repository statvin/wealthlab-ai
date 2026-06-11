"""Fixtures de teste — todas baseadas em dados sintéticos (sem rede)."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.marketdata.synthetic import SyntheticProvider

# Parâmetros "verdadeiros" usados para gerar os dados sintéticos. Os testes de
# estimação verificam que conseguimos recuperá-los.
TICKERS = ["AAA", "BBB"]
MU_ANUAL = np.array([0.10, 0.14])
SIGMA_ANUAL = np.array([0.18, 0.25])
CORR = np.array([[1.0, 0.30], [0.30, 1.0]])


@pytest.fixture(scope="session")
def params_verdadeiros() -> dict:
    """Os parâmetros que geraram os dados sintéticos."""
    return {
        "tickers": TICKERS,
        "mu_anual": MU_ANUAL,
        "sigma_anual": SIGMA_ANUAL,
        "corr": CORR,
    }


@pytest.fixture(scope="session")
def precos_sinteticos():
    """~50 anos de preços diários sintéticos (DataFrame datas × tickers).

    Histórico longo de propósito: aperta a precisão da estimativa da média
    (cujo erro-padrão cai com a raiz do nº de anos).
    """
    provider = SyntheticProvider(
        tickers=TICKERS,
        mu_anual=MU_ANUAL,
        sigma_anual=SIGMA_ANUAL,
        correlacao=CORR,
        preco_inicial=100.0,
        seed=123,
    )
    return provider.get_history(TICKERS, date(1974, 1, 1), date(2024, 1, 1))


@pytest.fixture
def params_rv_conhecidos() -> EstimatedParams:
    """EstimatedParams construído à mão (mensal), para testar o motor sem
    depender da etapa de estimação. μ e Σ mensais simples e bem-comportados."""
    mu_log_mensal = np.array([0.008, 0.010])           # ~9.6% / 12% a.a. log
    sigma_mensal = np.array([0.05, 0.07])
    corr = np.array([[1.0, 0.4], [0.4, 1.0]])
    cov_mensal = np.outer(sigma_mensal, sigma_mensal) * corr
    return EstimatedParams(
        tickers=["RV1", "RV2"],
        mu_log_mensal=mu_log_mensal,
        cov_mensal=cov_mensal,
        mu_log_aa=mu_log_mensal * 12,
        sigma_aa=sigma_mensal * np.sqrt(12),
        corr=corr,
    )
