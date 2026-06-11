"""Testes do gerador de retornos t-Student multivariada.

Verificam as três propriedades que importam:
  1. A covariância SIMULADA casa a covariância-alvo, INDEPENDENTE de df
     (é o efeito do reescalonamento por (df-2)/df).
  2. df controla a gordura da cauda: df baixo -> curtose alta; df alto -> normal.
  3. Reprodutibilidade e a guarda df > 2.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import kurtosis

from wealthlab_core.engine.returns import gerar_choques_tstudent

COV_ALVO = np.array([[0.0025, 0.0010], [0.0010, 0.0049]])  # (σ≈5% e 7%, ρ≈0.29)


def _amostra(df, n_cen=40_000, n_passos=12, seed=7):
    rng = np.random.default_rng(seed)
    choques = gerar_choques_tstudent(COV_ALVO, n_cen, n_passos, df, rng)
    return choques.reshape(-1, COV_ALVO.shape[0])  # (n_amostras, n_ativos)


def test_covariancia_bate_alvo_df_baixo():
    amostras = _amostra(df=5)
    cov_emp = np.cov(amostras, rowvar=False, ddof=1)
    np.testing.assert_allclose(cov_emp, COV_ALVO, rtol=0.05, atol=1e-4)


def test_covariancia_bate_alvo_df_alto():
    # Mesmo com df grande (quase normal), a covariância deve casar o alvo.
    amostras = _amostra(df=200)
    cov_emp = np.cov(amostras, rowvar=False, ddof=1)
    np.testing.assert_allclose(cov_emp, COV_ALVO, rtol=0.05, atol=1e-4)


def test_media_zero():
    amostras = _amostra(df=8)
    np.testing.assert_allclose(amostras.mean(axis=0), [0.0, 0.0], atol=2e-3)


def test_df_baixo_tem_cauda_mais_pesada_que_df_alto():
    k_baixo = kurtosis(_amostra(df=5)[:, 0], fisher=True)   # excesso de curtose
    k_alto = kurtosis(_amostra(df=200)[:, 0], fisher=True)
    # Cauda pesada (df=5) tem curtose bem maior; df alto ~ normal (excesso ~0).
    assert k_baixo > k_alto + 1.0
    assert abs(k_alto) < 0.5


def test_df_invalido_levanta():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        gerar_choques_tstudent(COV_ALVO, 10, 12, df=2.0, rng=rng)


def test_reprodutibilidade():
    a = gerar_choques_tstudent(COV_ALVO, 100, 12, 6, np.random.default_rng(42))
    b = gerar_choques_tstudent(COV_ALVO, 100, 12, 6, np.random.default_rng(42))
    np.testing.assert_array_equal(a, b)
