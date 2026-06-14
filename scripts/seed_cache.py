"""Popula o cache de preços com histórico SINTÉTICO dos tickers da carteira-modelo.

Por que existe: o `YahooFinanceProvider` é cache-first, então com o cache populado
o dashboard roda 100% offline (a demo não pode depender da API do Yahoo, que é
instável e tem rate limit). Em produção, bastaria deixar o cache baixar de verdade.

Uso (a partir da raiz do projeto):
    python scripts/seed_cache.py
"""

from __future__ import annotations

from datetime import date

import numpy as np

from wealthlab_core.marketdata.cache import SQLitePriceCache
from wealthlab_core.marketdata.synthetic import SyntheticProvider
from wealthlab_api.config import get_settings

# Tickers de renda variável da carteira-modelo do front (lib/defaultPortfolio.ts).
TICKERS = ["PETR4.SA", "IVVB11.SA", "BTC-USD"]
MU_ANUAL = np.array([0.12, 0.10, 0.35])
SIGMA_ANUAL = np.array([0.28, 0.18, 0.70])
CORR = np.array([[1.0, 0.35, 0.20], [0.35, 1.0, 0.25], [0.20, 0.25, 1.0]])


def main() -> None:
    settings = get_settings()
    cache = SQLitePriceCache(settings.cache_path)
    provider = SyntheticProvider(TICKERS, MU_ANUAL, SIGMA_ANUAL, CORR, seed=7)
    precos = provider.get_history(TICKERS, date(2010, 1, 1), date.today())
    cache.salvar(precos)
    print(
        f"Cache populado: {precos.shape[0]} pregões × {len(TICKERS)} tickers "
        f"em {settings.cache_path}"
    )


if __name__ == "__main__":
    main()
