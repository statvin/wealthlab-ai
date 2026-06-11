"""Provedor sintético de preços — usado nos testes (sem rede).

Gera histórico de preços a partir de parâmetros *conhecidos* (μ, σ, correlação),
o que nos permite verificar que a camada de estimação os recupera. É um GBM
multivariado simples (choques normais), de propósito: queremos um gerador
independente do motor de simulação (que usa t-Student), para que o teste de
estimação não seja circular.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from wealthlab_core.marketdata.provider import MarketDataProvider

# Pregões por ano (base diária). Útil para anualizar nos testes.
PREGOES_POR_ANO = 252


class SyntheticProvider(MarketDataProvider):
    """Gera preços diários log-normais com μ/σ/correlação especificados.

    Parâmetros são anualizados (como o usuário pensaria); convertemos para o
    passo diário internamente.
    """

    def __init__(
        self,
        tickers: list[str],
        mu_anual: np.ndarray,
        sigma_anual: np.ndarray,
        correlacao: np.ndarray,
        preco_inicial: float | np.ndarray = 100.0,
        seed: int = 0,
    ) -> None:
        self.tickers = list(tickers)
        self.mu_anual = np.asarray(mu_anual, dtype=float)
        self.sigma_anual = np.asarray(sigma_anual, dtype=float)
        self.correlacao = np.asarray(correlacao, dtype=float)
        self.preco_inicial = preco_inicial
        self.seed = seed

        n = len(self.tickers)
        if self.mu_anual.shape != (n,) or self.sigma_anual.shape != (n,):
            raise ValueError("mu_anual/sigma_anual devem ter shape (n_tickers,).")
        if self.correlacao.shape != (n, n):
            raise ValueError("correlacao deve ter shape (n_tickers, n_tickers).")

    def get_history(
        self,
        tickers: list[str],
        inicio: date,
        fim: date,
    ) -> pd.DataFrame:
        idx = pd.bdate_range(start=inicio, end=fim)  # dias úteis
        n_dias = len(idx)
        n = len(self.tickers)
        rng = np.random.default_rng(self.seed)

        # Passo diário: drift e covariância diários a partir dos anuais.
        dt = 1.0 / PREGOES_POR_ANO
        cov_diaria = (
            np.outer(self.sigma_anual, self.sigma_anual) * self.correlacao * dt
        )
        # Drift de log-preço com correção de Itô (-σ²/2), para que o μ anual
        # represente o retorno *esperado* (aritmético), padrão de GBM.
        drift_diario = (self.mu_anual - 0.5 * self.sigma_anual**2) * dt

        L = np.linalg.cholesky(cov_diaria)
        z = rng.standard_normal(size=(n_dias, n))
        log_ret = drift_diario + z @ L.T  # (n_dias, n)
        log_ret[0, :] = 0.0  # primeiro dia é o preço inicial

        precos0 = np.broadcast_to(
            np.asarray(self.preco_inicial, dtype=float), (n,)
        )
        precos = precos0 * np.exp(np.cumsum(log_ret, axis=0))

        # Devolvemos apenas as colunas pedidas (na ordem pedida).
        df = pd.DataFrame(precos, index=idx, columns=self.tickers)
        faltando = [t for t in tickers if t not in df.columns]
        if faltando:
            raise KeyError(f"tickers não gerados por este provider: {faltando}")
        return df[tickers]
