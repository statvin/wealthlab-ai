"""Termos contratuais de um papel de renda fixa.

A spec define `Asset { ticker, nome, classe }`. Renda fixa precisa de mais
informação para ser evoluída (taxa, indexador, duration). Em vez de poluir
`Asset`, anexamos um `FixedIncomeTerms` apenas aos ativos de classe
FIXED_INCOME_* (decisão (a) do alinhamento inicial).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator

from wealthlab_core.domain.enums import Indexador


class FixedIncomeTerms(BaseModel):
    """Parâmetros de um título de renda fixa.

    A semântica de `taxa_contratada` depende de `indexador` (ver `Indexador`):
      - CDI/SELIC : percentual do índice (1.0 = 100% do CDI).
      - IPCA      : juro real anual (0.06 = IPCA + 6% a.a.).
      - PREFIXADO : taxa nominal anual (0.11 = 11% a.a.).

    `duration_anos` é a duration (Macaulay/modificada ~ aproximadas no v1) usada
    para marcação a mercado de papéis IPCA+ sob choque de juros:
        ΔP/P ≈ −duration × Δy
    No carrego base (sem stress) ela não altera o acúmulo; entra na Fase 3.
    Pós-fixados têm duration efetiva ~0 (acompanham a taxa), por isso é opcional.
    """

    model_config = {"frozen": True}  # imutável: termos não mudam após criados

    indexador: Indexador
    taxa_contratada: float = Field(
        ...,
        description="Interpretação depende do indexador (ver docstring).",
    )
    duration_anos: float = Field(
        default=0.0,
        ge=0.0,
        description="Duration em anos. Relevante para IPCA+ (MtM no stress).",
    )
    vencimento: date | None = Field(
        default=None,
        description="Data de vencimento (opcional; informativa no v1).",
    )

    @model_validator(mode="after")
    def _coerencia(self) -> "FixedIncomeTerms":
        # Percentual de CDI/SELIC negativo ou nulo não faz sentido econômico.
        if self.indexador in (Indexador.CDI, Indexador.SELIC):
            if self.taxa_contratada <= 0:
                raise ValueError(
                    "Para CDI/SELIC, taxa_contratada é o percentual do índice "
                    "e deve ser > 0 (ex.: 1.0 = 100% do CDI)."
                )
        # IPCA+ sem duration é tecnicamente válido (duration=0 → sem risco MtM),
        # mas avisamos via duration default 0.0; deixamos passar de propósito.
        return self
