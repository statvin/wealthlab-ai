"""Testes do stress testing (Fase 3) — coerência Base vs. Stress."""

from __future__ import annotations

import numpy as np
import pytest

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
    RebalanceMode,
    SimulationConfig,
)
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.stress import (
    PRESETS,
    StressScenario,
    aplicar_correlacao_alvo,
    comparar_base_vs_stress,
    estressar_parametros,
    precos_com_haircut,
)

JUROS = PremissasJuros(selic_aa=0.10, ipca_aa=0.04)


def _params(tickers, sigma_m, corr, mu_m=None):
    sigma_m = np.asarray(sigma_m, float)
    corr = np.asarray(corr, float)
    mu_m = np.full(len(tickers), 0.008) if mu_m is None else np.asarray(mu_m, float)
    cov = np.outer(sigma_m, sigma_m) * corr
    return EstimatedParams(
        tickers=list(tickers),
        mu_log_mensal=mu_m,
        cov_mensal=cov,
        mu_log_aa=mu_m * 12,
        sigma_aa=sigma_m * np.sqrt(12),
        corr=corr,
    )


# --------------------------------------------------------------------------
# Correlações → 1
# --------------------------------------------------------------------------
def test_correlacao_intensidade_zero_nao_muda():
    corr = np.array([[1.0, 0.3], [0.3, 1.0]])
    out = aplicar_correlacao_alvo(corr, 0.0)
    np.testing.assert_allclose(out, corr, atol=1e-7)


def test_correlacao_intensidade_um_vai_para_um():
    corr = np.array([[1.0, 0.3, 0.1], [0.3, 1.0, 0.2], [0.1, 0.2, 1.0]])
    out = aplicar_correlacao_alvo(corr, 1.0)
    fora_diag = out[~np.eye(3, dtype=bool)]
    np.testing.assert_allclose(fora_diag, 1.0, atol=1e-6)


def test_correlacao_resultado_positiva_definida():
    corr = np.array([[1.0, 0.3, 0.1], [0.3, 1.0, 0.2], [0.1, 0.2, 1.0]])
    for inten in (0.0, 0.5, 0.9, 1.0):
        out = aplicar_correlacao_alvo(corr, inten)
        np.linalg.cholesky(out)  # levanta se não for PD


def test_correlacao_monotonica():
    corr = np.array([[1.0, 0.3], [0.3, 1.0]])
    baixa = aplicar_correlacao_alvo(corr, 0.3)[0, 1]
    alta = aplicar_correlacao_alvo(corr, 0.8)[0, 1]
    assert corr[0, 1] < baixa < alta


# --------------------------------------------------------------------------
# Estressar parâmetros
# --------------------------------------------------------------------------
def test_estressar_piora_vol_e_drift():
    base = _params(["A", "B"], [0.05, 0.06], [[1.0, 0.3], [0.3, 1.0]], mu_m=[0.01, 0.012])
    cen = PRESETS["2008"]
    s = estressar_parametros(base, cen)
    # vol sobe pelo multiplicador
    np.testing.assert_allclose(s.sigma_aa, base.sigma_aa * cen.vol_multiplicador)
    # drift cai
    np.testing.assert_allclose(s.mu_log_aa, base.mu_log_aa + cen.delta_drift_aa)
    assert (s.mu_log_aa < base.mu_log_aa).all()
    # correlação sobe
    assert s.corr[0, 1] > base.corr[0, 1]
    # covariância continua PD
    np.linalg.cholesky(s.cov_mensal)


def test_estressar_neutro_nao_muda():
    base = _params(["A", "B"], [0.05, 0.06], [[1.0, 0.3], [0.3, 1.0]])
    s = estressar_parametros(base, StressScenario(nome="neutro"))
    np.testing.assert_allclose(s.sigma_aa, base.sigma_aa, rtol=1e-6)
    np.testing.assert_allclose(s.mu_log_aa, base.mu_log_aa, rtol=1e-6)
    np.testing.assert_allclose(s.cov_mensal, base.cov_mensal, atol=1e-9)


def test_vol_da_carteira_sobe_no_stress():
    base = _params(["A", "B"], [0.05, 0.06], [[1.0, 0.3], [0.3, 1.0]])
    s = estressar_parametros(base, PRESETS["COVID-2020"])
    w = np.array([0.5, 0.5])
    vol_base = np.sqrt(w @ (base.cov_mensal * 12) @ w)
    vol_stress = np.sqrt(w @ (s.cov_mensal * 12) @ w)
    assert vol_stress > vol_base


# --------------------------------------------------------------------------
# Haircut do IPCA+ via duration
# --------------------------------------------------------------------------
def test_haircut_ipca_factor():
    cen = StressScenario(nome="x", choque_juros_ipca_aa=0.02)
    # duration 5 anos, Δy 2% -> queda ~10%
    np.testing.assert_allclose(cen.haircut_ipca(5.0), 0.90)
    # choque extremo é limitado a 0 (sem preço negativo)
    assert cen.haircut_ipca(100.0) == 0.0


def test_precos_com_haircut_atinge_so_ipca():
    acao = Asset(ticker="RV", nome="RV", classe=AssetClass.EQUITY_BR)
    ntnb = Asset(
        ticker="NTNB", nome="Tesouro IPCA+", classe=AssetClass.FIXED_INCOME_IPCA,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.IPCA, taxa_contratada=0.06, duration_anos=5.0),
    )
    pf = Portfolio(holdings=[Holding(asset=acao, quantidade=10), Holding(asset=ntnb, quantidade=1000)])
    cen = StressScenario(nome="x", choque_juros_ipca_aa=0.02)
    precos = precos_com_haircut(pf, cen, {"RV": 100.0, "NTNB": 1.0})
    assert precos["RV"] == 100.0          # ação não sofre
    np.testing.assert_allclose(precos["NTNB"], 0.90)  # IPCA+ leva o hit


# --------------------------------------------------------------------------
# Comparação Base vs. Stress (coerência)
# --------------------------------------------------------------------------
def test_comparacao_base_vs_stress_coerente():
    params = _params(["RV"], [0.06], [[1.0]], mu_m=[0.009])
    acao = Asset(ticker="RV", nome="RV", classe=AssetClass.EQUITY_BR)
    ntnb = Asset(
        ticker="NTNB", nome="Tesouro IPCA+", classe=AssetClass.FIXED_INCOME_IPCA,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.IPCA, taxa_contratada=0.06, duration_anos=5.0),
    )
    pf = Portfolio(holdings=[Holding(asset=acao, quantidade=10), Holding(asset=ntnb, quantidade=1000)])
    cfg = SimulationConfig(
        n_cenarios=5000, horizonte_anos=10.0, seed=3, rebalanceamento=RebalanceMode.NENHUM,
    )
    precos = {"RV": 100.0, "NTNB": 1.0}

    comp = comparar_base_vs_stress(
        pf, cfg, JUROS, PRESETS["Brasil-2015"], params_rv=params, precos_iniciais=precos,
    )

    r = comp.resumo
    # O regime de stress deve ser inequivocamente pior:
    assert r["p50_final"][1] < r["p50_final"][0]          # mediana cai
    assert r["var_95_1ano"][1] > r["var_95_1ano"][0]      # VaR sobe
    assert r["cvar_95_1ano"][1] > r["cvar_95_1ano"][0]    # CVaR sobe
    assert r["drawdown_pior"][1] >= r["drawdown_pior"][0]  # drawdown não melhora
    assert r["prob_ruina"][1] >= r["prob_ruina"][0]


def test_presets_sao_todos_adversos():
    assert set(PRESETS) == {"2008", "COVID-2020", "Estagflacao", "Brasil-2015"}
    for cen in PRESETS.values():
        assert cen.vol_multiplicador >= 1.0
        assert cen.delta_drift_aa <= 0.0
        assert 0.0 <= cen.intensidade_correlacao <= 1.0
