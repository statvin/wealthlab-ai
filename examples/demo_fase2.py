"""Demo da Fase 2 — análise de risco sobre a mesma carteira da Fase 1.

Execute:  python examples/demo_fase2.py
"""

from __future__ import annotations

from datetime import date

import numpy as np

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
    TargetAllocation,
)
from wealthlab_core.engine.estimation import estimar_parametros
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.metrics import analisar_risco
from wealthlab_core.marketdata.synthetic import SyntheticProvider


def main() -> None:
    tickers = ["PETR4.SA", "IVVB11.SA", "BTC"]
    provider = SyntheticProvider(
        tickers,
        mu_anual=np.array([0.12, 0.10, 0.35]),
        sigma_anual=np.array([0.28, 0.18, 0.70]),
        correlacao=np.array([[1.0, 0.35, 0.20], [0.35, 1.0, 0.25], [0.20, 0.25, 1.0]]),
        seed=7,
    )
    precos = provider.get_history(tickers, date(2004, 1, 1), date(2024, 1, 1))
    params = estimar_parametros(precos)

    assets = {
        "PETR4.SA": Asset(ticker="PETR4.SA", nome="Petrobras PN", classe=AssetClass.EQUITY_BR),
        "IVVB11.SA": Asset(ticker="IVVB11.SA", nome="S&P500 BRL", classe=AssetClass.EQUITY_INTL),
        "BTC": Asset(ticker="BTC", nome="Bitcoin", classe=AssetClass.CRYPTO),
        "CDB": Asset(
            ticker="CDB", nome="CDB 100% CDI", classe=AssetClass.FIXED_INCOME_POS,
            fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=1.0),
        ),
    }
    precos_iniciais = {"PETR4.SA": 38.0, "IVVB11.SA": 340.0, "BTC": 350_000.0, "CDB": 1.0}
    portfolio = Portfolio(
        holdings=[
            Holding(asset=assets["PETR4.SA"], quantidade=500),
            Holding(asset=assets["IVVB11.SA"], quantidade=100),
            Holding(asset=assets["BTC"], quantidade=0.05),
            Holding(asset=assets["CDB"], quantidade=30_000),
        ]
    )
    target = TargetAllocation(
        por_classe={
            AssetClass.EQUITY_BR: 0.25,
            AssetClass.EQUITY_INTL: 0.35,
            AssetClass.CRYPTO: 0.10,
            AssetClass.FIXED_INCOME_POS: 0.30,
        }
    )
    config = SimulationConfig(
        n_cenarios=10_000, horizonte_anos=30.0, seed=42, inflacao_aa=0.04,
        rebalanceamento=RebalanceMode.ANUAL_AO_ALVO, df_tstudent=6.0,
    )
    juros = PremissasJuros(selic_aa=0.105, ipca_aa=0.04)
    cashflow = CashFlowPlan(aporte_mensal=2_000.0)
    goal = FinancialGoal(valor_meta=3_000_000.0, prazo_anos=30.0)

    ra = analisar_risco(
        portfolio, config, juros, params_rv=params, cashflow=cashflow,
        target=target, precos_iniciais=precos_iniciais, goal=goal,
    )

    print("=== Risco de mercado (retorno da carteira em 1 ano, pesos atuais) ===")
    for nivel, vc in ra.var_cvar.items():
        print(f"  VaR {nivel:.0%}: {vc.var:6.2%}   CVaR {nivel:.0%}: {vc.cvar:6.2%}")
    print()
    print("=== Horizonte completo (30 anos, com aportes e rebalanceamento) ===")
    print(f"  Prob. de ruína:           {ra.prob_ruina:6.2%}")
    print(f"  Prob. de meta (R$ 3M):    {ra.prob_meta:6.2%}")
    print(f"  Drawdown médio/pior:      {ra.drawdown.medio:.2%} / {ra.drawdown.pior:.2%}")
    print()
    print("=== Contribuição ao risco (vol. anual = "
          f"{ra.contribuicao.vol_anual_carteira:.2%}) ===")
    for ticker, pctr in ra.contribuicao.ranking():
        print(f"  {ticker:10s} {pctr:6.1%}")
    print("  por classe:")
    for classe, pctr in sorted(ra.contribuicao.por_classe.items(), key=lambda x: -x[1]):
        print(f"    {classe.value:20s} {pctr:6.1%}")


if __name__ == "__main__":
    main()
