"""Testes do motor de simulação.

Estratégia: isolar cada mecanismo usando renda fixa DETERMINÍSTICA (selic/ipca
fixos), de modo que o resultado esperado seja calculável na mão. Só o teste de
mistura RV+RF usa o bloco estocástico.
"""

from __future__ import annotations

import ast
import inspect

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
from wealthlab_core.engine import simulator
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.simulator import simular_portfolio

JUROS_ZERO = PremissasJuros(selic_aa=0.0, ipca_aa=0.0)
JUROS_BASE = PremissasJuros(selic_aa=0.10, ipca_aa=0.04)


def _rf(ticker, indexador, taxa, classe):
    return Asset(
        ticker=ticker,
        nome=ticker,
        classe=classe,
        fixed_income_terms=FixedIncomeTerms(indexador=indexador, taxa_contratada=taxa),
    )


def _cfg(n_cen=200, anos=2.0, rebal=RebalanceMode.NENHUM, seed=42, infl=0.0):
    return SimulationConfig(
        n_cenarios=n_cen,
        horizonte_anos=anos,
        seed=seed,
        inflacao_aa=infl,
        rebalanceamento=rebal,
        df_tstudent=6.0,
    )


# --------------------------------------------------------------------------
# Guarda estrutural: nenhum loop sobre cenários no código do motor.
# --------------------------------------------------------------------------
def _nomes_no_no(no: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(no) if isinstance(n, ast.Name)}


def test_sem_loop_sobre_cenarios_no_codigo():
    # Analisa a AST (ignora docstrings/comentários): nenhum `for` pode iterar
    # sobre os cenários. Aceitamos loops sobre tempo (range), ativos, classes.
    for modulo in ("simulator", "returns", "fixed_income"):
        mod = __import__(f"wealthlab_core.engine.{modulo}", fromlist=[""])
        arvore = ast.parse(inspect.getsource(mod))
        for no in ast.walk(arvore):
            if isinstance(no, (ast.For, ast.comprehension)):
                alvo = _nomes_no_no(no.target)
                iteravel = _nomes_no_no(no.iter)
                proibidos = {"cenario", "cenarios"}
                assert not (alvo & proibidos), f"loop sobre cenário em {modulo}"
                assert not (iteravel & proibidos), f"itera sobre cenarios em {modulo}"


# --------------------------------------------------------------------------
# Renda fixa determinística: todas as trajetórias idênticas e fechadas.
# --------------------------------------------------------------------------
def test_renda_fixa_deterministica_cresce_composta():
    cdb = _rf("CDB", Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)  # 100% CDI = 10%a.a.
    pf = Portfolio(holdings=[Holding(asset=cdb, quantidade=1000.0)])
    cfg = _cfg(n_cen=50, anos=3.0, rebal=RebalanceMode.NENHUM)

    res = simular_portfolio(pf, cfg, JUROS_BASE)

    esperado = 1000.0 * (1.10 ** 3)  # carrego determinístico de 3 anos
    np.testing.assert_allclose(res.patrimonio_final, esperado, rtol=1e-9)
    # determinístico -> variância nula entre cenários
    assert res.patrimonio_final.std() < 1e-6
    assert not res.ruina_mask.any()


# --------------------------------------------------------------------------
# Fluxo de caixa puro (sem retorno): final = V0 + soma dos aportes.
# --------------------------------------------------------------------------
def test_aporte_sem_retorno_soma_exata():
    cdb = _rf("CDB", Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)
    pf = Portfolio(holdings=[Holding(asset=cdb, quantidade=1000.0)])
    cfg = _cfg(n_cen=10, anos=2.0)  # 24 passos
    cash = CashFlowPlan(aporte_mensal=100.0)

    res = simular_portfolio(pf, cfg, JUROS_ZERO, cashflow=cash)

    np.testing.assert_allclose(res.patrimonio_final, 1000.0 + 24 * 100.0, rtol=1e-12)


def test_saque_excessivo_causa_ruina():
    cdb = _rf("CDB", Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)
    pf = Portfolio(holdings=[Holding(asset=cdb, quantidade=1000.0)])
    cfg = _cfg(n_cen=10, anos=2.0)
    cash = CashFlowPlan(saque_mensal=200.0)  # zera em ~5 meses

    res = simular_portfolio(pf, cfg, JUROS_ZERO, cashflow=cash)

    assert res.ruina_mask.all()
    np.testing.assert_allclose(res.patrimonio_final, 0.0, atol=1e-9)


# --------------------------------------------------------------------------
# Rebalanceamento anual ao alvo: reseta os pesos por classe.
# --------------------------------------------------------------------------
def _carteira_duas_classes():
    pos = _rf("CDB", Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)   # 10% a.a.
    ipca = _rf("TD-IPCA", Indexador.IPCA, 0.10, AssetClass.FIXED_INCOME_IPCA)  # ~14.4% a.a.
    return Portfolio(
        holdings=[Holding(asset=pos, quantidade=1000.0), Holding(asset=ipca, quantidade=1000.0)]
    )


def test_rebalanceamento_reseta_pesos_ao_alvo():
    pf = _carteira_duas_classes()
    target = TargetAllocation(
        por_classe={AssetClass.FIXED_INCOME_POS: 0.5, AssetClass.FIXED_INCOME_IPCA: 0.5}
    )
    cfg = _cfg(n_cen=10, anos=2.0, rebal=RebalanceMode.ANUAL_AO_ALVO)

    res = simular_portfolio(pf, cfg, JUROS_BASE, target=target)

    # horizonte de 2 anos -> rebalance no passo 24 (último): pesos 50/50.
    v0 = res.valores_finais_por_ativo[:, 0]
    v1 = res.valores_finais_por_ativo[:, 1]
    np.testing.assert_allclose(v0, v1, rtol=1e-9)


def test_buy_and_hold_diverge_dos_pesos():
    pf = _carteira_duas_classes()
    cfg = _cfg(n_cen=10, anos=2.0, rebal=RebalanceMode.NENHUM)

    res = simular_portfolio(pf, cfg, JUROS_BASE)

    # Sem rebalance, o ativo de maior taxa (IPCA+) pesa mais ao final.
    v0 = res.valores_finais_por_ativo[:, 0]
    v1 = res.valores_finais_por_ativo[:, 1]
    assert (v1 > v0 * 1.05).all()


# --------------------------------------------------------------------------
# Patrimônio real x nominal.
# --------------------------------------------------------------------------
def test_patrimonio_real_deflaciona():
    cdb = _rf("CDB", Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)
    pf = Portfolio(holdings=[Holding(asset=cdb, quantidade=1000.0)])
    cfg = _cfg(n_cen=10, anos=2.0, infl=0.05)

    res = simular_portfolio(pf, cfg, JUROS_BASE)

    nominal = res.patrimonio_final
    real = res.trajetorias_reais()[:, -1]
    np.testing.assert_allclose(real, nominal / (1.05 ** 2), rtol=1e-9)
    assert (real < nominal).all()


# --------------------------------------------------------------------------
# Reprodutibilidade por seed (bloco estocástico).
# --------------------------------------------------------------------------
def test_reprodutibilidade_por_seed(params_rv_conhecidos):
    acao = Asset(ticker="RV1", nome="RV1", classe=AssetClass.EQUITY_BR)
    pf = Portfolio(holdings=[Holding(asset=acao, quantidade=1000.0)])
    params = params_rv_conhecidos.reordenar(["RV1"])

    cfg_a = _cfg(n_cen=500, anos=5.0, seed=2024)
    cfg_b = _cfg(n_cen=500, anos=5.0, seed=2024)
    cfg_c = _cfg(n_cen=500, anos=5.0, seed=9999)

    ra = simular_portfolio(pf, cfg_a, JUROS_BASE, params_rv=params)
    rb = simular_portfolio(pf, cfg_b, JUROS_BASE, params_rv=params)
    rc = simular_portfolio(pf, cfg_c, JUROS_BASE, params_rv=params)

    np.testing.assert_array_equal(ra.trajetorias_nominais, rb.trajetorias_nominais)
    assert not np.array_equal(ra.trajetorias_nominais, rc.trajetorias_nominais)


# --------------------------------------------------------------------------
# Mistura renda variável + renda fixa (caminho completo).
# --------------------------------------------------------------------------
def test_mistura_rv_rf_roda(precos_sinteticos):
    from wealthlab_core.engine.estimation import estimar_parametros

    params = estimar_parametros(precos_sinteticos)  # tickers AAA, BBB
    aaa = Asset(ticker="AAA", nome="AAA", classe=AssetClass.EQUITY_BR)
    bbb = Asset(ticker="BBB", nome="BBB", classe=AssetClass.EQUITY_INTL)
    cdb = _rf("CDB", Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)
    pf = Portfolio(
        holdings=[
            Holding(asset=aaa, quantidade=10.0),
            Holding(asset=bbb, quantidade=10.0),
            Holding(asset=cdb, quantidade=2000.0),
        ]
    )
    target = TargetAllocation(
        por_classe={
            AssetClass.EQUITY_BR: 0.4,
            AssetClass.EQUITY_INTL: 0.4,
            AssetClass.FIXED_INCOME_POS: 0.2,
        }
    )
    cfg = _cfg(n_cen=2000, anos=10.0, rebal=RebalanceMode.ANUAL_AO_ALVO, infl=0.04)
    cash = CashFlowPlan(aporte_mensal=500.0)
    precos = {"AAA": 100.0, "BBB": 100.0, "CDB": 1.0}

    res = simular_portfolio(
        pf, cfg, JUROS_BASE, params_rv=params, cashflow=cash, target=target,
        precos_iniciais=precos,
    )

    assert res.trajetorias_nominais.shape == (2000, cfg.n_passos + 1)
    p5, p50, p95 = res.percentis_finais([5, 50, 95])
    assert p5 < p50 < p95
    assert p50 > 0
