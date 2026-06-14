"""Testes das métricas de risco (Fase 2).

Critério de aceite: as métricas batem com casos sintéticos de resposta conhecida
(fórmulas fechadas normais/lognormais e construções determinísticas).
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    CashFlowPlan,
    FinancialGoal,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
    RebalanceMode,
    SimulationConfig,
)
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.metrics import (
    analisar_risco,
    contribuicao_ao_risco,
    estatisticas_drawdown,
    matriz_covariancia_anual,
    max_drawdown_por_trajetoria,
    pesos_iniciais,
    prob_meta,
    prob_ruina,
    simular_retornos_1ano,
    var_cvar,
)
from wealthlab_core.engine.simulator import simular_portfolio

JUROS = PremissasJuros(selic_aa=0.10, ipca_aa=0.04)
JUROS_ZERO = PremissasJuros(selic_aa=0.0, ipca_aa=0.0)


def _params_um_ativo(mu_m=0.008, sigma_m=0.05, ticker="RV") -> EstimatedParams:
    cov = np.array([[sigma_m**2]])
    return EstimatedParams(
        tickers=[ticker],
        mu_log_mensal=np.array([mu_m]),
        cov_mensal=cov,
        mu_log_aa=np.array([mu_m * 12]),
        sigma_aa=np.array([sigma_m * np.sqrt(12)]),
        corr=np.array([[1.0]]),
    )


def _cdb(ticker="CDB", pct=1.0):
    return Asset(
        ticker=ticker,
        nome=ticker,
        classe=AssetClass.FIXED_INCOME_POS,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=pct),
    )


# --------------------------------------------------------------------------
# VaR / CVaR contra fórmula fechada normal.
# --------------------------------------------------------------------------
def test_var_cvar_bate_normal_analitico():
    mu, sigma = 0.08, 0.20
    rng = np.random.default_rng(1)
    amostras = rng.normal(mu, sigma, size=2_000_000)
    res = var_cvar(amostras, niveis=(0.95, 0.99))

    for nivel in (0.95, 0.99):
        p = 1.0 - nivel
        z = norm.ppf(p)
        var_teorico = -(mu + sigma * z)
        cvar_teorico = -(mu - sigma * norm.pdf(z) / p)
        np.testing.assert_allclose(res[nivel].var, var_teorico, rtol=0.03)
        np.testing.assert_allclose(res[nivel].cvar, cvar_teorico, rtol=0.03)


def test_cvar_maior_que_var_e_99_maior_que_95():
    rng = np.random.default_rng(2)
    amostras = rng.normal(0.05, 0.25, size=1_000_000)
    res = var_cvar(amostras, niveis=(0.95, 0.99))
    # ES (cauda média) é sempre pior que o VaR; 99% é pior que 95%.
    assert res[0.95].cvar > res[0.95].var
    assert res[0.99].var > res[0.95].var
    assert res[0.99].cvar > res[0.95].cvar


# --------------------------------------------------------------------------
# VaR de 1 ano da carteira contra a fórmula lognormal (df alto ≈ normal).
# --------------------------------------------------------------------------
def test_var_1ano_bate_lognormal():
    mu_m, sigma_m = 0.008, 0.05
    params = _params_um_ativo(mu_m, sigma_m)
    acao = Asset(ticker="RV", nome="RV", classe=AssetClass.EQUITY_BR)
    pf = Portfolio(holdings=[Holding(asset=acao, quantidade=1000.0)])
    cfg = SimulationConfig(
        n_cenarios=10, horizonte_anos=1.0, seed=5,
        rebalanceamento=RebalanceMode.NENHUM, df_tstudent=300.0,  # ~normal
    )

    ret = simular_retornos_1ano(pf, cfg, JUROS, params_rv=params, n_cenarios=200_000)
    res = var_cvar(ret, niveis=(0.95,))

    mu_a, sigma_a = mu_m * 12, sigma_m * np.sqrt(12)
    var_teorico = 1.0 - np.exp(mu_a + sigma_a * norm.ppf(0.05))
    np.testing.assert_allclose(res[0.95].var, var_teorico, rtol=0.05)


def test_var_1ano_cresce_com_cauda_pesada():
    params = _params_um_ativo()
    acao = Asset(ticker="RV", nome="RV", classe=AssetClass.EQUITY_BR)
    pf = Portfolio(holdings=[Holding(asset=acao, quantidade=1000.0)])

    def _var(df):
        cfg = SimulationConfig(
            n_cenarios=10, horizonte_anos=1.0, seed=5,
            rebalanceamento=RebalanceMode.NENHUM, df_tstudent=df,
        )
        ret = simular_retornos_1ano(pf, cfg, JUROS, params_rv=params, n_cenarios=200_000)
        return var_cvar(ret, niveis=(0.99,))[0.99]

    pesada = _var(4.0)
    leve = _var(200.0)
    # Cauda pesada (df baixo) implica perdas extremas maiores.
    assert pesada.var > leve.var
    assert pesada.cvar > leve.cvar


# --------------------------------------------------------------------------
# Drawdown contra valores calculados na mão.
# --------------------------------------------------------------------------
def test_drawdown_caso_conhecido():
    traj = np.array([[100.0, 120.0, 90.0, 150.0, 80.0]])
    dd = max_drawdown_por_trajetoria(traj)
    # pior queda: de 150 para 80 = 1 - 80/150 = 0.4667.
    np.testing.assert_allclose(dd, [1.0 - 80.0 / 150.0])


def test_drawdown_monotonico_e_zero():
    traj = np.array([[100.0, 110.0, 121.0, 133.0]])
    dd = max_drawdown_por_trajetoria(traj)
    np.testing.assert_allclose(dd, [0.0])


def test_estatisticas_drawdown_agrega():
    traj = np.array([[100.0, 50.0, 100.0], [100.0, 100.0, 100.0]])
    est = estatisticas_drawdown(traj)
    # trajetória 1: dd 0.5; trajetória 2: dd 0.0.
    np.testing.assert_allclose(est.pior, 0.5)
    np.testing.assert_allclose(est.medio, 0.25)


# --------------------------------------------------------------------------
# Ruína e meta em construções determinísticas.
# --------------------------------------------------------------------------
def test_prob_ruina_zero_e_um():
    pf = Portfolio(holdings=[Holding(asset=_cdb(), quantidade=1000.0)])
    cfg = SimulationConfig(
        n_cenarios=20, horizonte_anos=2.0, rebalanceamento=RebalanceMode.NENHUM
    )

    # Sem saque -> nunca ruína.
    r1 = simular_portfolio(pf, cfg, JUROS)
    assert prob_ruina(r1) == 0.0

    # Saque grande com juro zero -> sempre ruína.
    r2 = simular_portfolio(pf, cfg, JUROS_ZERO, cashflow=CashFlowPlan(saque_mensal=200.0))
    assert prob_ruina(r2) == 1.0


def test_prob_meta_determinista():
    pf = Portfolio(holdings=[Holding(asset=_cdb(), quantidade=1000.0)])
    cfg = SimulationConfig(
        n_cenarios=20, horizonte_anos=10.0, rebalanceamento=RebalanceMode.NENHUM
    )
    res = simular_portfolio(pf, cfg, JUROS)   # final determinístico = 1000*1.1^10 ≈ 2593.7

    assert prob_meta(res, FinancialGoal(valor_meta=2000.0, prazo_anos=10.0)) == 1.0
    assert prob_meta(res, FinancialGoal(valor_meta=3000.0, prazo_anos=10.0)) == 0.0


# --------------------------------------------------------------------------
# Contribuição ao risco.
# --------------------------------------------------------------------------
def test_contribuicao_simetrica_meio_a_meio():
    v, c = 0.04, 0.012
    cov = np.array([[v, c], [c, v]])
    pesos = np.array([0.5, 0.5])
    classes = [AssetClass.EQUITY_BR, AssetClass.EQUITY_BR]
    cr = contribuicao_ao_risco(cov, pesos, ["A", "B"], classes)
    np.testing.assert_allclose(cr.pctr, [0.5, 0.5])
    np.testing.assert_allclose(sum(cr.pctr), 1.0)
    np.testing.assert_allclose(cr.por_classe[AssetClass.EQUITY_BR], 1.0)


def test_contribuicao_renda_fixa_e_zero():
    # Ativo 0 com risco, ativo 1 (RF) sem variância.
    cov = np.array([[0.04, 0.0], [0.0, 0.0]])
    pesos = np.array([0.5, 0.5])
    classes = [AssetClass.EQUITY_BR, AssetClass.FIXED_INCOME_POS]
    cr = contribuicao_ao_risco(cov, pesos, ["RV", "RF"], classes)
    np.testing.assert_allclose(cr.pctr, [1.0, 0.0])
    assert cr.por_classe[AssetClass.FIXED_INCOME_POS] == 0.0


def test_contribuicao_carteira_sem_risco():
    cov = np.zeros((2, 2))
    pesos = np.array([0.5, 0.5])
    classes = [AssetClass.FIXED_INCOME_POS, AssetClass.FIXED_INCOME_IPCA]
    cr = contribuicao_ao_risco(cov, pesos, ["A", "B"], classes)
    assert cr.vol_anual_carteira == 0.0
    np.testing.assert_allclose(cr.pctr, [0.0, 0.0])


def test_matriz_cov_zera_renda_fixa(params_rv_conhecidos):
    aaa = Asset(ticker="RV1", nome="RV1", classe=AssetClass.EQUITY_BR)
    cdb = _cdb()
    pf = Portfolio(holdings=[Holding(asset=aaa, quantidade=10.0), Holding(asset=cdb, quantidade=1000.0)])
    cov = matriz_covariancia_anual(pf, params_rv_conhecidos.reordenar(["RV1"]))
    # Linha/coluna da RF (índice 1) deve ser toda zero.
    assert np.all(cov[1, :] == 0.0) and np.all(cov[:, 1] == 0.0)
    assert cov[0, 0] > 0.0


# --------------------------------------------------------------------------
# Orquestrador completo.
# --------------------------------------------------------------------------
def test_analisar_risco_end_to_end(precos_sinteticos):
    from wealthlab_core.engine.estimation import estimar_parametros

    params = estimar_parametros(precos_sinteticos)  # AAA, BBB
    aaa = Asset(ticker="AAA", nome="AAA", classe=AssetClass.EQUITY_BR)
    bbb = Asset(ticker="BBB", nome="BBB", classe=AssetClass.EQUITY_INTL)
    cdb = _cdb()
    pf = Portfolio(
        holdings=[
            Holding(asset=aaa, quantidade=10.0),
            Holding(asset=bbb, quantidade=10.0),
            Holding(asset=cdb, quantidade=2000.0),
        ]
    )
    cfg = SimulationConfig(
        n_cenarios=3000, horizonte_anos=10.0, rebalanceamento=RebalanceMode.NENHUM,
    )
    precos = {"AAA": 100.0, "BBB": 100.0, "CDB": 1.0}
    goal = FinancialGoal(valor_meta=50_000.0, prazo_anos=10.0)

    ra = analisar_risco(
        pf, cfg, JUROS, params_rv=params, precos_iniciais=precos, goal=goal,
    )

    assert set(ra.var_cvar) == {0.95, 0.99}
    assert ra.var_cvar[0.99].var >= ra.var_cvar[0.95].var
    assert 0.0 <= ra.prob_ruina <= 1.0
    assert 0.0 <= ra.prob_meta <= 1.0
    assert 0.0 <= ra.drawdown.medio <= ra.drawdown.pior <= 1.0
    # A RF deve contribuir pouquíssimo para o risco; a soma dos PCTR é 1.
    np.testing.assert_allclose(sum(ra.contribuicao.pctr), 1.0)
    assert ra.contribuicao.por_classe[AssetClass.FIXED_INCOME_POS] < 0.05
