"""Estimação de μ, σ e correlação a partir do histórico (renda variável).

Convenções importantes (leia — é a base de tudo):

1. Trabalhamos em **log-retornos**. O drift que estimamos (média dos log-retornos)
   já é a *deriva geométrica*, líquida da "drenagem" da volatilidade — ou seja,
   já embute o termo −σ²/2 do GBM. Por isso, ao acumular log-retornos no motor,
   NÃO aplicamos nenhuma correção de Itô extra. E, com df→∞, recuperamos o
   lognormal clássico de forma exata.

2. Estimamos no passo **diário** e anualizamos por escala (média ×252, cov ×252),
   assumindo retornos i.i.d. — a hipótese padrão. Em seguida "mensalizamos"
   (÷12) para alimentar o motor, que roda em passo mensal. A correlação é
   invariante à escala temporal sob i.i.d., então pode ser lida em qualquer
   frequência.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from wealthlab_core.domain.config import PASSOS_POR_ANO

# Pregões por ano (base diária) para anualização.
PREGOES_POR_ANO = 252


@dataclass(frozen=True)
class EstimatedParams:
    """Parâmetros estimados da renda variável, prontos para o motor.

    - `mu_log_mensal` / `cov_mensal`: o que o motor consome (passo mensal).
    - `mu_log_aa` / `sigma_aa` / `corr`: versões anualizadas para exibição.

    `mu_log_aa` é a deriva *log* anualizada (geométrica), não o retorno
    aritmético esperado. O retorno aritmético seria mu_log_aa + 0.5·σ².
    """

    tickers: list[str]
    mu_log_mensal: np.ndarray  # (n,)
    cov_mensal: np.ndarray     # (n, n)
    mu_log_aa: np.ndarray      # (n,)
    sigma_aa: np.ndarray       # (n,)
    corr: np.ndarray           # (n, n)

    @property
    def n_ativos(self) -> int:
        return len(self.tickers)

    def reordenar(self, tickers: list[str]) -> "EstimatedParams":
        """Reordena/seleciona os parâmetros para casar a ordem de `tickers`.

        O motor recebe os ativos na ordem da carteira; os parâmetros podem ter
        sido estimados em outra ordem. Esta função garante o alinhamento.
        """
        idx = [self.tickers.index(t) for t in tickers]
        return EstimatedParams(
            tickers=list(tickers),
            mu_log_mensal=self.mu_log_mensal[idx],
            cov_mensal=self.cov_mensal[np.ix_(idx, idx)],
            mu_log_aa=self.mu_log_aa[idx],
            sigma_aa=self.sigma_aa[idx],
            corr=self.corr[np.ix_(idx, idx)],
        )


def estimar_parametros(
    precos: pd.DataFrame,
    pregoes_por_ano: int = PREGOES_POR_ANO,
) -> EstimatedParams:
    """Estima parâmetros a partir de um DataFrame de preços (datas × tickers).

    Limpa NaNs, calcula log-retornos diários, e devolve os momentos mensais e
    anualizados. Exige ao menos 2 retornos (3 preços) para estimar covariância.
    """
    precos = precos.dropna(how="any").sort_index()
    if precos.shape[0] < 3:
        raise ValueError(
            "histórico insuficiente: são necessários ao menos 3 preços limpos."
        )

    tickers = list(precos.columns)
    log_precos = np.log(precos.to_numpy(dtype=float))
    log_ret = np.diff(log_precos, axis=0)  # (T-1, n) — log-retornos diários

    mu_d = log_ret.mean(axis=0)                       # (n,)
    cov_d = np.atleast_2d(np.cov(log_ret, rowvar=False, ddof=1))  # (n, n)
    sigma_d = np.sqrt(np.diag(cov_d))

    # Correlação (invariante à escala temporal sob i.i.d.).
    corr = cov_d / np.outer(sigma_d, sigma_d)
    np.fill_diagonal(corr, 1.0)  # robustez numérica

    # Anualização por escala (i.i.d.): média ×N, covariância ×N.
    mu_log_aa = mu_d * pregoes_por_ano
    cov_aa = cov_d * pregoes_por_ano
    sigma_aa = np.sqrt(np.diag(cov_aa))

    # Mensalização para o motor (passo mensal).
    mu_log_mensal = mu_log_aa / PASSOS_POR_ANO
    cov_mensal = cov_aa / PASSOS_POR_ANO

    return EstimatedParams(
        tickers=tickers,
        mu_log_mensal=mu_log_mensal,
        cov_mensal=cov_mensal,
        mu_log_aa=mu_log_aa,
        sigma_aa=sigma_aa,
        corr=corr,
    )
