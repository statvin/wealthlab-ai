"""Testes do módulo de aposentadoria (Fase 6).

Usa carteira 100% renda fixa (determinística) para que sucesso seja 0/1 e as
propriedades sejam verificáveis sem ruído de Monte Carlo.
"""

from __future__ import annotations

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
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.retirement import analisar_aposentadoria

JUROS = PremissasJuros(selic_aa=0.10, ipca_aa=0.04)


def _carteira_rf():
    cdb = Asset(
        ticker="CDB", nome="CDB 100% CDI", classe=AssetClass.FIXED_INCOME_POS,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=1.0),
    )
    return Portfolio(holdings=[Holding(asset=cdb, quantidade=100000.0)])


def _cfg():
    return SimulationConfig(
        n_cenarios=50, horizonte_anos=1.0, seed=1, rebalanceamento=RebalanceMode.NENHUM
    )


def _analisar(saque):
    return analisar_aposentadoria(
        _carteira_rf(), _cfg(), JUROS,
        idade_atual=40, idade_aposentadoria=60, idade_final=85,
        aporte_mensal=1000.0, saque_mensal_desejado=saque,
        n_cenarios_busca=50, iteracoes_busca=12,
    )


def test_acumulacao_cresce_patrimonio():
    r = _analisar(0.0)
    # Sem saque, RF só cresce -> sucesso total e patrimônio na aposentadoria > inicial.
    assert r.prob_sucesso == 1.0
    assert r.patrimonio_aposentadoria["p50"] > 100000.0


def test_saque_absurdo_falha():
    r = _analisar(1_000_000.0)  # saque mensal gigante
    assert r.prob_sucesso < 0.9


def test_saque_sustentavel_positivo_e_coerente():
    r = _analisar(2000.0)
    assert r.saque_sustentavel > 0.0
    # O saque sustentável deve, ele próprio, sustentar o plano (sucesso ≥ alvo).
    rs = analisar_aposentadoria(
        _carteira_rf(), _cfg(), JUROS,
        idade_atual=40, idade_aposentadoria=60, idade_final=85,
        aporte_mensal=1000.0, saque_mensal_desejado=r.saque_sustentavel * 0.95,
        n_cenarios_busca=50, iteracoes_busca=12,
    )
    assert rs.prob_sucesso >= r.alvo_sucesso


def test_reprodutibilidade():
    a = _analisar(2000.0)
    b = _analisar(2000.0)
    assert a.saque_sustentavel == b.saque_sustentavel
    assert a.prob_sucesso == b.prob_sucesso
