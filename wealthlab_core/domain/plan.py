"""Planos do usuário: fluxos de caixa, alocação-alvo e meta financeira."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from wealthlab_core.domain.enums import AssetClass

# Tolerância para "soma de pesos = 1" (erro de ponto flutuante / arredondamento).
_TOL_PESOS = 1e-6


class CashFlowPlan(BaseModel):
    """Aportes e saques mensais ao longo do horizonte.

    Decisão (b): valores **nominais constantes** por padrão. O flag
    `corrigir_por_inflacao` permite, opcionalmente, fazer os fluxos crescerem
    com a inflação (mais realista para aposentadoria), mas fica desligado no v1.

    `inicio_mes`/`fim_mes` são offsets em meses (0-based, inclusivos). `None` em
    `fim_mes` significa "até o fim do horizonte". Permitem, por exemplo, aportar
    nos primeiros 20 anos e sacar depois.
    """

    model_config = {"frozen": True}

    aporte_mensal: float = Field(default=0.0, ge=0.0)
    saque_mensal: float = Field(default=0.0, ge=0.0)
    inicio_mes: int = Field(default=0, ge=0)
    fim_mes: int | None = Field(default=None, ge=0)
    corrigir_por_inflacao: bool = False

    @model_validator(mode="after")
    def _janela_valida(self) -> "CashFlowPlan":
        if self.fim_mes is not None and self.fim_mes < self.inicio_mes:
            raise ValueError("fim_mes não pode ser anterior a inicio_mes.")
        return self


class TargetAllocation(BaseModel):
    """Alocação-alvo por classe de ativo. A soma dos pesos deve ser 1.0."""

    model_config = {"frozen": True}

    por_classe: dict[AssetClass, float]

    @model_validator(mode="after")
    def _pesos_validos(self) -> "TargetAllocation":
        if not self.por_classe:
            raise ValueError("por_classe não pode ser vazio.")
        if any(p < 0 for p in self.por_classe.values()):
            raise ValueError("pesos-alvo não podem ser negativos.")
        soma = sum(self.por_classe.values())
        if abs(soma - 1.0) > _TOL_PESOS:
            raise ValueError(
                f"soma dos pesos-alvo deve ser 1.0 (atual: {soma:.6f})."
            )
        return self


class FinancialGoal(BaseModel):
    """Meta financeira: atingir `valor_meta` em `prazo_anos`."""

    model_config = {"frozen": True}

    valor_meta: float = Field(..., gt=0)
    prazo_anos: float = Field(..., gt=0)
