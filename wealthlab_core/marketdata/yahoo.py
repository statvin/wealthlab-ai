"""Provedor Yahoo Finance (com cache-first).

Implementado para uso real, mas **não exercitado nos testes** (decisão (c)): o
núcleo é validado com dados sintéticos, sem rede. O import de `yfinance` é
preguiçoso, de modo que o pacote roda/testa mesmo sem a dependência instalada.

B3 usa sufixo `.SA` (PETR4.SA, VALE3.SA, IVVB11.SA). A convenção aqui é que o
*chamador* já passe o ticker com o sufixo correto; este provider não adivinha a
bolsa do papel.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from wealthlab_core.marketdata.cache import SQLitePriceCache
from wealthlab_core.marketdata.provider import MarketDataProvider
from wealthlab_core.utils import get_logger

logger = get_logger("wealthlab_core.marketdata.yahoo")


class YahooFinanceProvider(MarketDataProvider):
    """Busca fechamentos ajustados no Yahoo, usando o cache SQLite como fonte
    primária (a rede só é tocada no que faltar)."""

    def __init__(self, cache: SQLitePriceCache | None = None) -> None:
        self.cache = cache or SQLitePriceCache()

    def get_history(
        self,
        tickers: list[str],
        inicio: date,
        fim: date,
    ) -> pd.DataFrame:
        # 1) Tenta o cache primeiro.
        em_cache = self.cache.carregar(tickers, inicio, fim)
        faltando = [t for t in tickers if t not in em_cache.columns]

        if not faltando:
            logger.info("yahoo: %d tickers servidos do cache.", len(tickers))
            return em_cache[tickers]

        # 2) Baixa o que faltar e atualiza o cache.
        logger.info("yahoo: baixando %s da rede (faltavam no cache).", faltando)
        baixado = self._baixar(faltando, inicio, fim)
        if not baixado.empty:
            self.cache.salvar(baixado)

        # 3) Combina cache + recém-baixado, alinhando datas.
        combinado = pd.concat([em_cache, baixado], axis=1)
        cols = [t for t in tickers if t in combinado.columns]
        return combinado[cols].dropna(how="all").sort_index()

    @staticmethod
    def _baixar(tickers: list[str], inicio: date, fim: date) -> pd.DataFrame:
        try:
            import yfinance as yf  # import preguiçoso: extra opcional [market]
        except ImportError as exc:  # pragma: no cover - caminho de rede
            raise RuntimeError(
                "yfinance não está instalado. Instale o extra: pip install "
                "'wealthlab-core[market]'. (O núcleo não precisa dele.)"
            ) from exc

        dados = yf.download(
            tickers,
            start=inicio.isoformat(),
            end=fim.isoformat(),
            auto_adjust=True,
            progress=False,
        )
        # yfinance retorna colunas multiíndice quando há >1 ticker.
        if isinstance(dados.columns, pd.MultiIndex):
            close = dados["Close"]
        else:
            close = dados[["Close"]].rename(columns={"Close": tickers[0]})
        return close.dropna(how="all")
