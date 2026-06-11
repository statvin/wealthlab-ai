"""Testes da estimação: recuperar μ/σ/correlação conhecidos dos dados sintéticos.

Lembrete do porquê das tolerâncias: σ e correlação são estimados com baixo erro
em 50 anos de dados; a média (drift) é intrinsecamente mais ruidosa (erro-padrão
~ σ/√anos), por isso usamos atol maior nela.

Nota conceitual importante: o gerador sintético usa drift com correção de Itô
(−σ²/2), logo o que a estimação recupera é a DERIVA LOG (geométrica):
    mu_log_aa ≈ mu_anual − 0.5·σ²
e não o retorno aritmético. Isso é exatamente o que o motor deve consumir.
"""

from __future__ import annotations

import numpy as np

from wealthlab_core.engine.estimation import estimar_parametros


def test_recupera_volatilidade(precos_sinteticos, params_verdadeiros):
    p = estimar_parametros(precos_sinteticos)
    np.testing.assert_allclose(
        p.sigma_aa, params_verdadeiros["sigma_anual"], rtol=0.06
    )


def test_recupera_correlacao(precos_sinteticos, params_verdadeiros):
    p = estimar_parametros(precos_sinteticos)
    np.testing.assert_allclose(p.corr, params_verdadeiros["corr"], atol=0.04)


def test_recupera_deriva_log_com_correcao_ito(precos_sinteticos, params_verdadeiros):
    p = estimar_parametros(precos_sinteticos)
    mu_log_esperado = (
        params_verdadeiros["mu_anual"] - 0.5 * params_verdadeiros["sigma_anual"] ** 2
    )
    np.testing.assert_allclose(p.mu_log_aa, mu_log_esperado, atol=0.05)


def test_mensalizacao_consistente(precos_sinteticos):
    p = estimar_parametros(precos_sinteticos)
    # mensal × 12 == anual (escala i.i.d.).
    np.testing.assert_allclose(p.mu_log_mensal * 12, p.mu_log_aa, rtol=1e-12)
    np.testing.assert_allclose(np.diag(p.cov_mensal) * 12, p.sigma_aa**2, rtol=1e-12)


def test_historico_insuficiente_levanta():
    import pandas as pd

    df = pd.DataFrame({"AAA": [100.0, 101.0]})
    try:
        estimar_parametros(df)
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass
