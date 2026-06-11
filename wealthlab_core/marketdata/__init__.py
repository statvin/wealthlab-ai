"""Camada de dados de mercado (desacoplada da fonte)."""

from wealthlab_core.marketdata.cache import SQLitePriceCache
from wealthlab_core.marketdata.provider import MarketDataProvider
from wealthlab_core.marketdata.synthetic import SyntheticProvider
from wealthlab_core.marketdata.yahoo import YahooFinanceProvider

__all__ = [
    "MarketDataProvider",
    "SyntheticProvider",
    "SQLitePriceCache",
    "YahooFinanceProvider",
]
