"""Testes da recomendação de rebalanceamento (Fase 6)."""

from __future__ import annotations

import numpy as np

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
    TargetAllocation,
)
from wealthlab_core.engine.rebalance import recomendar_rebalanceamento


def _acao(ticker, valor):
    return Holding(asset=Asset(ticker=ticker, nome=ticker, classe=AssetClass.EQUITY_BR), quantidade=valor)


def _cdb(valor):
    return Holding(
        asset=Asset(
            ticker="CDB", nome="CDB", classe=AssetClass.FIXED_INCOME_POS,
            fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=1.0),
        ),
        quantidade=valor,
    )


def _por_classe(rec, classe):
    return next(d for d in rec.por_classe if d.classe == classe)


def test_rebalanceamento_caso_conhecido():
    # Atual 60/40, alvo 50/50, total 100k -> vender 10k em ações, comprar 10k em RF.
    pf = Portfolio(holdings=[_acao("PETR4.SA", 60000), _cdb(40000)])
    target = TargetAllocation(
        por_classe={AssetClass.EQUITY_BR: 0.5, AssetClass.FIXED_INCOME_POS: 0.5}
    )
    rec = recomendar_rebalanceamento(pf, target)

    assert rec.valor_total == 100000
    np.testing.assert_allclose(_por_classe(rec, AssetClass.EQUITY_BR).delta, -10000)
    np.testing.assert_allclose(_por_classe(rec, AssetClass.FIXED_INCOME_POS).delta, 10000)

    trade_acao = next(t for t in rec.trades if t.ticker == "PETR4.SA")
    trade_cdb = next(t for t in rec.trades if t.ticker == "CDB")
    assert trade_acao.acao == "vender" and trade_acao.valor == 10000
    assert trade_cdb.acao == "comprar" and trade_cdb.valor == 10000
    np.testing.assert_allclose(rec.turnover, 0.10)


def test_rebalanceamento_ja_no_alvo():
    pf = Portfolio(holdings=[_acao("PETR4.SA", 50000), _cdb(50000)])
    target = TargetAllocation(
        por_classe={AssetClass.EQUITY_BR: 0.5, AssetClass.FIXED_INCOME_POS: 0.5}
    )
    rec = recomendar_rebalanceamento(pf, target)
    assert all(t.acao == "manter" for t in rec.trades)
    np.testing.assert_allclose(rec.turnover, 0.0, atol=1e-9)


def test_rebalanceamento_distribui_pro_rata_na_classe():
    # Duas ações na mesma classe (30k e 10k) + RF 60k; alvo 50% ações / 50% RF.
    pf = Portfolio(
        holdings=[_acao("AAA", 30000), _acao("BBB", 10000), _cdb(60000)]
    )
    target = TargetAllocation(
        por_classe={AssetClass.EQUITY_BR: 0.5, AssetClass.FIXED_INCOME_POS: 0.5}
    )
    rec = recomendar_rebalanceamento(pf, target)
    # Classe ações precisa subir de 40k para 50k (+10k), distribuído 75%/25%.
    ta = next(t for t in rec.trades if t.ticker == "AAA")
    tb = next(t for t in rec.trades if t.ticker == "BBB")
    np.testing.assert_allclose(ta.valor, 7500)
    np.testing.assert_allclose(tb.valor, 2500)
    assert ta.acao == "comprar" and tb.acao == "comprar"
