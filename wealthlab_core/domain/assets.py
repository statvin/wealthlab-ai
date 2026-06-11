"""Ativos, posições e carteira, com as validações de carteira exigidas na spec.

Validações cobertas:
  - ticker vazio                 -> Asset
  - quantidade negativa/nula     -> Holding
  - carteira vazia               -> Portfolio
  - ativo duplicado              -> Portfolio
  - (soma de pesos-alvo ≠ 1      -> TargetAllocation, em plan.py)
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from wealthlab_core.domain.enums import CLASSES_RENDA_FIXA, AssetClass
from wealthlab_core.domain.fixed_income import FixedIncomeTerms


class Asset(BaseModel):
    """Um ativo investível.

    Renda fixa carrega `fixed_income_terms`; renda variável não. A coerência
    entre `classe` e a presença dos termos é validada aqui, para que o motor
    nunca receba, por exemplo, um IPCA+ sem duration.
    """

    model_config = {"frozen": True}

    ticker: str = Field(..., description="Identificador (B3 usa sufixo .SA).")
    nome: str = Field(..., description="Nome legível do ativo.")
    classe: AssetClass
    fixed_income_terms: FixedIncomeTerms | None = None

    @field_validator("ticker")
    @classmethod
    def _ticker_nao_vazio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("ticker não pode ser vazio.")
        return v

    @model_validator(mode="after")
    def _coerencia_classe_termos(self) -> "Asset":
        eh_renda_fixa = self.classe in CLASSES_RENDA_FIXA
        if eh_renda_fixa and self.fixed_income_terms is None:
            raise ValueError(
                f"Ativo de classe {self.classe.value} exige fixed_income_terms."
            )
        if not eh_renda_fixa and self.fixed_income_terms is not None:
            raise ValueError(
                f"Ativo de classe {self.classe.value} não deve ter "
                "fixed_income_terms (apenas renda fixa)."
            )
        return self


class Holding(BaseModel):
    """Posição: um ativo e a quantidade detida.

    O valor inicial em R$ de cada posição é `quantidade * preço`, onde o preço
    vem do market data (renda variável) ou é o PU/valor unitário do papel
    (renda fixa). No núcleo trabalhamos com o vetor de valores iniciais já
    calculado, para manter o motor desacoplado da fonte de preço.
    """

    model_config = {"frozen": True}

    asset: Asset
    quantidade: float = Field(
        ...,
        gt=0,
        description="Quantidade detida; deve ser > 0 (negativa/nula é inválida).",
    )


class Portfolio(BaseModel):
    """Carteira: lista de posições, sem duplicidade de ticker."""

    holdings: list[Holding] = Field(..., min_length=1)

    @field_validator("holdings")
    @classmethod
    def _carteira_nao_vazia(cls, v: list[Holding]) -> list[Holding]:
        if len(v) == 0:
            raise ValueError("carteira não pode ser vazia.")
        return v

    @model_validator(mode="after")
    def _sem_duplicados(self) -> "Portfolio":
        tickers = [h.asset.ticker for h in self.holdings]
        duplicados = {t for t in tickers if tickers.count(t) > 1}
        if duplicados:
            raise ValueError(
                f"ativos duplicados na carteira: {sorted(duplicados)}."
            )
        return self

    @property
    def tickers(self) -> list[str]:
        return [h.asset.ticker for h in self.holdings]

    @property
    def assets(self) -> list[Asset]:
        return [h.asset for h in self.holdings]
