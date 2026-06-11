"""Cache SQLite do histórico de preços.

yfinance é instável e tem rate limit; a demo não pode depender da API online.
Este cache persiste o histórico baixado em SQLite e serve como fonte primária
nas próximas execuções. Também pode ser empacotado como snapshot.

Schema (uma linha por (ticker, data)):
    precos(ticker TEXT, data TEXT(ISO), close REAL, PRIMARY KEY(ticker, data))
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date

import pandas as pd

from wealthlab_core.utils import get_logger

logger = get_logger("wealthlab_core.marketdata.cache")


class SQLitePriceCache:
    """Persistência simples de séries de fechamento ajustado."""

    def __init__(self, caminho: str | None = None) -> None:
        self.caminho = caminho or os.getenv(
            "WEALTHLAB_CACHE_PATH", "data/cache/market.sqlite"
        )
        pasta = os.path.dirname(self.caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        self._criar_schema()

    def _conectar(self) -> sqlite3.Connection:
        return sqlite3.connect(self.caminho)

    def _criar_schema(self) -> None:
        with self._conectar() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS precos (
                    ticker TEXT NOT NULL,
                    data   TEXT NOT NULL,
                    close  REAL NOT NULL,
                    PRIMARY KEY (ticker, data)
                )
                """
            )

    def salvar(self, precos: pd.DataFrame) -> None:
        """Grava (upsert) um DataFrame de preços (índice=datas, colunas=tickers)."""
        registros = []
        for ticker in precos.columns:
            serie = precos[ticker].dropna()
            for dt, valor in serie.items():
                registros.append((ticker, pd.Timestamp(dt).date().isoformat(), float(valor)))
        if not registros:
            return
        with self._conectar() as con:
            con.executemany(
                "INSERT OR REPLACE INTO precos (ticker, data, close) VALUES (?, ?, ?)",
                registros,
            )
        logger.info("cache: %d pontos salvos (%d tickers).", len(registros), precos.shape[1])

    def carregar(
        self,
        tickers: list[str],
        inicio: date,
        fim: date,
    ) -> pd.DataFrame:
        """Lê os tickers no intervalo. Retorna DataFrame (datas x tickers)."""
        with self._conectar() as con:
            placeholders = ",".join("?" for _ in tickers)
            query = (
                f"SELECT ticker, data, close FROM precos "
                f"WHERE ticker IN ({placeholders}) AND data BETWEEN ? AND ? "
                f"ORDER BY data"
            )
            params = [*tickers, inicio.isoformat(), fim.isoformat()]
            df = pd.read_sql_query(query, con, params=params)

        if df.empty:
            return pd.DataFrame(columns=tickers)

        df["data"] = pd.to_datetime(df["data"])
        wide = df.pivot(index="data", columns="ticker", values="close")
        # Reordena colunas conforme pedido; mantém só os tickers existentes.
        cols = [t for t in tickers if t in wide.columns]
        return wide[cols].sort_index()

    def tickers_disponiveis(self) -> set[str]:
        with self._conectar() as con:
            cur = con.execute("SELECT DISTINCT ticker FROM precos")
            return {row[0] for row in cur.fetchall()}
