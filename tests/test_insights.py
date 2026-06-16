"""Testes dos insights por regras (Fase 6) — cada insight rastreável a uma métrica."""

from __future__ import annotations

import numpy as np

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    CashFlowPlan,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
)
from wealthlab_core.engine.insights import gerar_insights
from wealthlab_core.engine.metrics import ContribuicaoRisco, Drawdown, RiskAnalysis, VaRCVaR


def _risk(prob_meta, prob_ruina, dd_pior, ordem, pctr, por_classe):
    return RiskAnalysis(
        var_cvar={0.95: VaRCVaR(0.95, 0.1, 0.15)},
        prob_ruina=prob_ruina,
        prob_meta=prob_meta,
        drawdown=Drawdown(medio=0.2, mediano=0.18, pior=dd_pior),
        contribuicao=ContribuicaoRisco(
            ordem=ordem,
            pctr=np.array(pctr),
            contrib_vol=np.array(pctr),
            vol_anual_carteira=0.3,
            por_classe=por_classe,
        ),
    )


def _carteira_cripto():
    btc = Asset(ticker="BTC", nome="Bitcoin", classe=AssetClass.CRYPTO)
    cdb = Asset(
        ticker="CDB", nome="CDB", classe=AssetClass.FIXED_INCOME_POS,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=1.0),
    )
    # BTC 60k, CDB 40k -> cripto 60% (concentração + alerta de cripto)
    return Portfolio(holdings=[Holding(asset=btc, quantidade=60000), Holding(asset=cdb, quantidade=40000)])


def test_insights_disparam_e_sao_rastreaveis():
    pf = _carteira_cripto()
    risk = _risk(
        prob_meta=0.92, prob_ruina=0.20, dd_pior=0.60,
        ordem=["BTC", "CDB"], pctr=[0.7, 0.3],
        por_classe={AssetClass.CRYPTO: 0.7, AssetClass.FIXED_INCOME_POS: 0.3},
    )
    ins = gerar_insights(pf, risk)
    cats = {i.categoria for i in ins}
    assert {"meta", "concentracao", "cripto", "risco", "saque", "drawdown"} <= cats

    # Toda afirmação carrega métrica + valor (rastreabilidade).
    for i in ins:
        assert i.metrica and isinstance(i.valor, float)

    meta = next(i for i in ins if i.categoria == "meta")
    assert meta.severidade == "positivo" and meta.metrica == "prob_meta" and meta.valor == 0.92
    cripto = next(i for i in ins if i.categoria == "cripto")
    assert cripto.severidade == "alerta"


def test_meta_baixa_vira_atencao():
    pf = _carteira_cripto()
    risk = _risk(0.30, 0.0, 0.2, ["BTC", "CDB"], [0.4, 0.6],
                 {AssetClass.CRYPTO: 0.3, AssetClass.FIXED_INCOME_POS: 0.7})
    ins = gerar_insights(pf, risk)
    meta = next(i for i in ins if i.categoria == "meta")
    assert meta.severidade == "atencao" and meta.valor == 0.30


def test_taxa_de_retirada_alta():
    pf = _carteira_cripto()
    risk = _risk(0.9, 0.0, 0.2, ["BTC", "CDB"], [0.5, 0.5],
                 {AssetClass.CRYPTO: 0.1, AssetClass.FIXED_INCOME_POS: 0.9})
    # saque 1000/mês sobre 100k = 12% a.a. -> bem acima dos ~4%.
    cash = CashFlowPlan(saque_mensal=1000.0)
    ins = gerar_insights(pf, risk, cashflow=cash, valor_inicial=100000.0)
    taxa = next(i for i in ins if i.metrica == "taxa_retirada")
    np.testing.assert_allclose(taxa.valor, 0.12)
