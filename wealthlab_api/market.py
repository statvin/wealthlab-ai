"""Injeção do provedor de market data (dependency do FastAPI).

No app real usamos o YahooFinanceProvider com cache SQLite (cache-first). Nos
testes, esta dependency é sobrescrita por um provedor sintético — assim a API é
testada offline e de forma determinística.
"""

from __future__ import annotations

from wealthlab_core.marketdata import MarketDataProvider, SQLitePriceCache, YahooFinanceProvider
from wealthlab_api.config import get_settings


def get_market_provider() -> MarketDataProvider:
    cache = SQLitePriceCache(get_settings().cache_path)
    return YahooFinanceProvider(cache)
