"""Demo da Fase 3 — comparação Base vs. Stress, varrendo os presets.

Execute:  python examples/demo_fase3.py
"""

from __future__ import annotations

from datetime import date

import numpy as np

from wealthlab_core.domain import (
    Asset,
    AssetClass,
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
from wealthlab_core.engine.stress import PRESETS, comparar_base_vs_stress
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

    petr = Asset(ticker="PETR4.SA", nome="Petrobras PN", classe=AssetClass.EQUITY_BR)
    ivv = Asset(ticker="IVVB11.SA", nome="S&P500 BRL", classe=AssetClass.EQUITY_INTL)
    btc = Asset(ticker="BTC", nome="Bitcoin", classe=AssetClass.CRYPTO)
    ntnb = Asset(
        ticker="NTNB", nome="Tesouro IPCA+ 2035", classe=AssetClass.FIXED_INCOME_IPCA,
        fixed_income_terms=FixedIncomeTerms(indexador=Indexador.IPCA, taxa_contratada=0.06, duration_anos=7.0),
    )
    pf = Portfolio(
        holdings=[
            Holding(asset=petr, quantidade=500),
            Holding(asset=ivv, quantidade=100),
            Holding(asset=btc, quantidade=0.05),
            Holding(asset=ntnb, quantidade=30_000),
        ]
    )
    target = TargetAllocation(
        por_classe={
            AssetClass.EQUITY_BR: 0.25,
            AssetClass.EQUITY_INTL: 0.30,
            AssetClass.CRYPTO: 0.10,
            AssetClass.FIXED_INCOME_IPCA: 0.35,
        }
    )
    config = SimulationConfig(
        n_cenarios=10_000, horizonte_anos=20.0, seed=42, inflacao_aa=0.04,
        rebalanceamento=RebalanceMode.ANUAL_AO_ALVO, df_tstudent=6.0,
    )
    juros = PremissasJuros(selic_aa=0.105, ipca_aa=0.04)
    precos_iniciais = {"PETR4.SA": 38.0, "IVVB11.SA": 340.0, "BTC": 350_000.0, "NTNB": 1.0}

    rotulos = {
        "p50_final": ("Patrimônio P50 (R$)", "money"),
        "var_95_1ano": ("VaR 95% 1 ano", "pct"),
        "cvar_95_1ano": ("CVaR 95% 1 ano", "pct"),
        "drawdown_pior": ("Drawdown pior caso", "pct"),
        "prob_ruina": ("Prob. de ruína", "pct"),
    }

    for nome, cen in PRESETS.items():
        comp = comparar_base_vs_stress(
            pf, config, juros, cen, params_rv=params, target=target,
            precos_iniciais=precos_iniciais,
        )
        print(f"\n=== {nome}  ({cen.descricao}) ===")
        print(f"{'Métrica':22s} {'Base':>16s} {'Stress':>16s}")
        for chave, (rotulo, fmt) in rotulos.items():
            base, stress = comp.resumo[chave]
            if fmt == "money":
                print(f"{rotulo:22s} {base:>16,.0f} {stress:>16,.0f}")
            else:
                print(f"{rotulo:22s} {base:>15.2%} {stress:>15.2%}")


if __name__ == "__main__":
    main()
