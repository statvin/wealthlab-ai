"""Testes das validações de domínio (Pydantic)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
    TargetAllocation,
)


def _acao(ticker="PETR4.SA") -> Asset:
    return Asset(ticker=ticker, nome="Petrobras PN", classe=AssetClass.EQUITY_BR)


def _cdb() -> Asset:
    return Asset(
        ticker="CDB-XYZ",
        nome="CDB 100% CDI",
        classe=AssetClass.FIXED_INCOME_POS,
        fixed_income_terms=FixedIncomeTerms(
            indexador=Indexador.CDI, taxa_contratada=1.0
        ),
    )


def test_ticker_vazio_invalido():
    with pytest.raises(ValidationError):
        Asset(ticker="  ", nome="x", classe=AssetClass.EQUITY_BR)


def test_quantidade_negativa_invalida():
    with pytest.raises(ValidationError):
        Holding(asset=_acao(), quantidade=-1.0)


def test_quantidade_zero_invalida():
    with pytest.raises(ValidationError):
        Holding(asset=_acao(), quantidade=0.0)


def test_carteira_vazia_invalida():
    with pytest.raises(ValidationError):
        Portfolio(holdings=[])


def test_ativo_duplicado_invalido():
    h = Holding(asset=_acao(), quantidade=10)
    with pytest.raises(ValidationError, match="duplicad"):
        Portfolio(holdings=[h, Holding(asset=_acao(), quantidade=5)])


def test_renda_fixa_exige_termos():
    with pytest.raises(ValidationError, match="fixed_income_terms"):
        Asset(ticker="CDB", nome="x", classe=AssetClass.FIXED_INCOME_POS)


def test_renda_variavel_nao_aceita_termos():
    with pytest.raises(ValidationError):
        Asset(
            ticker="PETR4.SA",
            nome="x",
            classe=AssetClass.EQUITY_BR,
            fixed_income_terms=FixedIncomeTerms(
                indexador=Indexador.CDI, taxa_contratada=1.0
            ),
        )


def test_percentual_cdi_deve_ser_positivo():
    with pytest.raises(ValidationError):
        FixedIncomeTerms(indexador=Indexador.CDI, taxa_contratada=0.0)


def test_target_allocation_soma_um_ok():
    ta = TargetAllocation(
        por_classe={AssetClass.EQUITY_BR: 0.6, AssetClass.FIXED_INCOME_POS: 0.4}
    )
    assert abs(sum(ta.por_classe.values()) - 1.0) < 1e-9


def test_target_allocation_soma_diferente_de_um_invalida():
    with pytest.raises(ValidationError, match="1.0"):
        TargetAllocation(
            por_classe={AssetClass.EQUITY_BR: 0.6, AssetClass.FIXED_INCOME_POS: 0.5}
        )


def test_target_allocation_peso_negativo_invalido():
    with pytest.raises(ValidationError):
        TargetAllocation(
            por_classe={AssetClass.EQUITY_BR: 1.2, AssetClass.FIXED_INCOME_POS: -0.2}
        )


def test_carteira_valida_constroi():
    pf = Portfolio(
        holdings=[Holding(asset=_acao(), quantidade=100), Holding(asset=_cdb(), quantidade=5000)]
    )
    assert pf.tickers == ["PETR4.SA", "CDB-XYZ"]
