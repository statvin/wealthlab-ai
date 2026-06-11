"""Geração de retornos de renda variável: t-Student multivariada, vetorizada.

ESTA É A CAMADA 1 DA VETORIZAÇÃO (a "proibida de ter loop de cenário").
Geramos a matriz inteira de choques correlacionados de uma só vez, para todos os
`n_cenarios × n_passos × n_ativos`, via Cholesky × amostras t-Student.

-------------------------------------------------------------------------------
POR QUE t-STUDENT (e não normal)?
Retornos de mercado têm caudas gordas: crises acontecem mais do que a normal
prevê. A t-Student com `df` graus de liberdade captura isso; `df` baixo = cauda
mais pesada. Com df→∞ ela converge para a normal (caso lognormal clássico).

A SUTILEZA DO REESCALONAMENTO (importante para o estudo):
Uma t-Student multivariada com `df` g.l. e matriz de escala Σ tem covariância
    Cov = df/(df-2) · Σ        (finita só para df > 2).
Se usássemos Σ = cov_mensal diretamente, a volatilidade simulada viria inflada
pelo fator df/(df-2). Para que a covariância SIMULADA case exatamente a
ESTIMADA — independentemente de `df` —, usamos a escala
    Σ_ajustada = cov_mensal · (df-2)/df.
Assim você controla a *gordura da cauda* (via df) SEM mexer na volatilidade-alvo.

COMO AMOSTRAR (representação por mistura de escala):
Uma t multivariada padrão pode ser escrita como
    t = z / sqrt(g/df),  com z ~ N(0, I)  e  g ~ χ²(df),
onde g é COMPARTILHADO entre os ativos (um por cenário-passo). Esse g comum é o
que gera *dependência de cauda*: nos meses de choque extremo, todos os ativos
afundam juntos — exatamente o comportamento de crise. Depois aplicamos a
Cholesky de Σ_ajustada para impor a estrutura de correlação.
-------------------------------------------------------------------------------
"""

from __future__ import annotations

import numpy as np


def gerar_choques_tstudent(
    cov_mensal: np.ndarray,
    n_cenarios: int,
    n_passos: int,
    df: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Choques correlacionados de média zero, t-Student multivariada.

    Retorna array shape `(n_cenarios, n_passos, n_ativos)` cuja covariância por
    passo é exatamente `cov_mensal` (graças ao reescalonamento), com caudas
    governadas por `df`.

    100% vetorizado: nenhum loop sobre cenários.
    """
    if df <= 2:
        raise ValueError("df deve ser > 2 (variância da t-Student finita).")

    cov_mensal = np.atleast_2d(np.asarray(cov_mensal, dtype=float))
    n = cov_mensal.shape[0]

    # Escala ajustada para que Cov simulada == cov_mensal.
    cov_ajustada = cov_mensal * ((df - 2.0) / df)

    # Cholesky (uma única vez): L tal que L·Lᵀ = cov_ajustada.
    L = np.linalg.cholesky(cov_ajustada)  # (n, n) triangular inferior

    # z ~ N(0, I): (n_cenarios, n_passos, n_ativos)
    z = rng.standard_normal(size=(n_cenarios, n_passos, n))

    # g ~ χ²(df), COMPARTILHADO entre ativos (eixo de ativos = 1) -> dep. de cauda.
    g = rng.chisquare(df, size=(n_cenarios, n_passos, 1))

    # t multivariada padrão (escala identidade, cov = df/(df-2)·I).
    t_padrao = z / np.sqrt(g / df)

    # Impõe correlação: x = t_padrao · Lᵀ  ->  Cov(x) = L·(df/(df-2)·I)·Lᵀ = cov_mensal.
    # (matmul faz broadcast sobre os dois primeiros eixos; sem loop de cenário.)
    choques = t_padrao @ L.T
    return choques


def gerar_log_retornos_rv(
    mu_log_mensal: np.ndarray,
    cov_mensal: np.ndarray,
    n_cenarios: int,
    n_passos: int,
    df: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Log-retornos mensais de renda variável = deriva + choque t-Student.

    `mu_log_mensal` (n,) entra por broadcasting no último eixo. O resultado são
    log-retornos; o motor os converte em fatores via exp() e acumula.
    """
    mu = np.asarray(mu_log_mensal, dtype=float)
    choques = gerar_choques_tstudent(cov_mensal, n_cenarios, n_passos, df, rng)
    return mu + choques  # (n_cenarios, n_passos, n_ativos)
