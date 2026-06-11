"""Testes da renda fixa (carrego determinístico)."""

from __future__ import annotations

import numpy as np

from wealthlab_core.domain import Asset, AssetClass, FixedIncomeTerms, Indexador
from wealthlab_core.engine.fixed_income import (
    PremissasJuros,
    fator_mensal_constante,
    taxa_anual_carrego,
)

PREMISSAS = PremissasJuros(selic_aa=0.10, ipca_aa=0.04)


def _ativo_rf(indexador, taxa, classe):
    return Asset(
        ticker=f"RF-{indexador.value}",
        nome="RF",
        classe=classe,
        fixed_income_terms=FixedIncomeTerms(indexador=indexador, taxa_contratada=taxa),
    )


def test_cdi_100pct():
    a = _ativo_rf(Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)
    assert taxa_anual_carrego(a, PREMISSAS) == 0.10


def test_cdi_110pct():
    a = _ativo_rf(Indexador.CDI, 1.10, AssetClass.FIXED_INCOME_POS)
    np.testing.assert_allclose(taxa_anual_carrego(a, PREMISSAS), 0.11)


def test_ipca_mais_6():
    a = _ativo_rf(Indexador.IPCA, 0.06, AssetClass.FIXED_INCOME_IPCA)
    # (1+0.04)·(1+0.06) − 1 = 0.1024
    np.testing.assert_allclose(taxa_anual_carrego(a, PREMISSAS), 0.1024)


def test_prefixado():
    a = _ativo_rf(Indexador.PREFIXADO, 0.11, AssetClass.FIXED_INCOME_POS)
    np.testing.assert_allclose(taxa_anual_carrego(a, PREMISSAS), 0.11)


def test_fator_mensal_compoe_para_o_anual():
    a = _ativo_rf(Indexador.CDI, 1.0, AssetClass.FIXED_INCOME_POS)
    fator = fator_mensal_constante(a, PREMISSAS)
    # 12 meses compostos reproduzem a taxa anual.
    np.testing.assert_allclose(fator**12, 1.10, rtol=1e-12)
