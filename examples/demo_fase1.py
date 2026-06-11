"""Demo da Fase 1 — fluxo completo, ponta a ponta, com dados sintéticos.

Roda sem rede: usamos o SyntheticProvider para gerar um histórico, estimamos os
parâmetros, montamos uma carteira RV+RF e simulamos 10.000 cenários por 30 anos.

Execute:  python examples/demo_fase1.py
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
from wealthlab_core.engine.simulator import simular_portfolio
from wealthlab_core.marketdata.synthetic import SyntheticProvider


def main() -> None:
    # 1) Histórico sintético para 3 ativos de renda variável (sem rede).
    #    Em produção isto viria do YahooFinanceProvider (PETR4.SA, IVVB11.SA, ...).
    tickers = ["PETR4.SA", "IVVB11.SA", "BTC"]
    mu_anual = np.array([0.12, 0.10, 0.35])       # cripto com retorno esperado alto
    sigma_anual = np.array([0.28, 0.18, 0.70])    # ...e volatilidade altíssima
    corr = np.array(
        [
            [1.00, 0.35, 0.20],
            [0.35, 1.00, 0.25],
            [0.20, 0.25, 1.00],
        ]
    )
    provider = SyntheticProvider(tickers, mu_anual, sigma_anual, corr, seed=7)
    precos = provider.get_history(tickers, date(2004, 1, 1), date(2024, 1, 1))

    # 2) Estima μ/σ/correlação (em log-retornos) a partir do histórico.
    params = estimar_parametros(precos)
    print("Parâmetros estimados (anualizados):")
    for t, mu, sig in zip(params.tickers, params.mu_log_aa, params.sigma_aa):
        print(f"  {t:10s}  deriva log {mu:+.2%}   vol {sig:.2%}")
    print()

    # 3) Carteira: 3 ativos de RV + um CDB pós-fixado (100% do CDI).
    assets = {
        "PETR4.SA": Asset(ticker="PETR4.SA", nome="Petrobras PN", classe=AssetClass.EQUITY_BR),
        "IVVB11.SA": Asset(ticker="IVVB11.SA", nome="S&P500 BRL", classe=AssetClass.EQUITY_INTL),
        "BTC": Asset(ticker="BTC", nome="Bitcoin", classe=AssetClass.CRYPTO),
        "CDB": Asset(
            ticker="CDB",
            nome="CDB 100% CDI",
            classe=AssetClass.FIXED_INCOME_POS,
            fixed_income_terms=FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=1.0),
        ),
    }
    precos_iniciais = {"PETR4.SA": 38.0, "IVVB11.SA": 340.0, "BTC": 350_000.0, "CDB": 1.0}
    portfolio = Portfolio(
        holdings=[
            Holding(asset=assets["PETR4.SA"], quantidade=500),    # ~R$ 19k
            Holding(asset=assets["IVVB11.SA"], quantidade=100),   # ~R$ 34k
            Holding(asset=assets["BTC"], quantidade=0.05),        # ~R$ 17,5k
            Holding(asset=assets["CDB"], quantidade=30_000),      # R$ 30k
        ]
    )

    # 4) Alvo por classe (rebalanceamento anual) e plano de aportes.
    target = TargetAllocation(
        por_classe={
            AssetClass.EQUITY_BR: 0.25,
            AssetClass.EQUITY_INTL: 0.35,
            AssetClass.CRYPTO: 0.10,
            AssetClass.FIXED_INCOME_POS: 0.30,
        }
    )
    cashflow = CashFlowPlan(aporte_mensal=2_000.0)  # aporta R$ 2k/mês, nominal
    config = SimulationConfig(
        n_cenarios=10_000,
        horizonte_anos=30.0,
        seed=42,
        inflacao_aa=0.04,
        rebalanceamento=RebalanceMode.ANUAL_AO_ALVO,
        df_tstudent=6.0,         # caudas gordas (df baixo)
    )
    juros = PremissasJuros(selic_aa=0.105, ipca_aa=0.04)

    # 5) Simula.
    res = simular_portfolio(
        portfolio, config, juros,
        params_rv=params, cashflow=cashflow, target=target,
        precos_iniciais=precos_iniciais,
    )

    # 6) KPIs (o que a Fase 2 vai formalizar; aqui já dá para sentir o motor).
    inicial = res.trajetorias_nominais[0, 0]
    p10, p50, p90 = res.percentis_finais([10, 50, 90])
    p10r, p50r, p90r = res.percentis_finais([10, 50, 90], real=True)
    meta = FinancialGoal(valor_meta=3_000_000.0, prazo_anos=30.0)
    prob_meta = float((res.patrimonio_final >= meta.valor_meta).mean())
    prob_ruina = float(res.ruina_mask.mean())

    print(f"Patrimônio inicial:           R$ {inicial:,.0f}")
    print("Patrimônio final em 30 anos (nominal):")
    print(f"  P10 R$ {p10:,.0f}  |  P50 R$ {p50:,.0f}  |  P90 R$ {p90:,.0f}")
    print("Patrimônio final em 30 anos (REAL, hoje):")
    print(f"  P10 R$ {p10r:,.0f}  |  P50 R$ {p50r:,.0f}  |  P90 R$ {p90r:,.0f}")
    print(f"Prob. de atingir R$ {meta.valor_meta:,.0f}:   {prob_meta:.1%}")
    print(f"Prob. de ruína (tocar zero):  {prob_ruina:.2%}")


if __name__ == "__main__":
    main()
