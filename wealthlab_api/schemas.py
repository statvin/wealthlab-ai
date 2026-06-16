"""DTOs Pydantic v2 (transporte). Separados do ORM e do domínio do motor.

Reaproveitamos os enums do domínio (são str-enums) para validar entrada com os
mesmos valores que o motor entende.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from wealthlab_core.domain.enums import AssetClass, Indexador, RebalanceMode


# --------------------------- Entrada: carteira ----------------------------
class FixedIncomeTermsDTO(BaseModel):
    indexador: Indexador
    taxa_contratada: float
    duration_anos: float = 0.0
    vencimento: str | None = None


class AssetDTO(BaseModel):
    ticker: str
    nome: str
    classe: AssetClass
    fixed_income_terms: FixedIncomeTermsDTO | None = None


class HoldingDTO(BaseModel):
    asset: AssetDTO
    quantidade: float = Field(gt=0)
    preco_inicial: float = Field(default=1.0, gt=0)


class PortfolioCreate(BaseModel):
    nome: str = "Carteira"
    holdings: list[HoldingDTO] = Field(min_length=1)


class HoldingOut(BaseModel):
    ticker: str
    nome: str
    classe: AssetClass
    quantidade: float
    preco_inicial: float


class PortfolioOut(BaseModel):
    id: int
    nome: str
    holdings: list[HoldingOut]


# --------------------------- Entrada: simulação ---------------------------
class PremissasJurosDTO(BaseModel):
    selic_aa: float = 0.10
    ipca_aa: float = 0.04


class CashFlowDTO(BaseModel):
    aporte_mensal: float = 0.0
    saque_mensal: float = 0.0
    inicio_mes: int = 0
    fim_mes: int | None = None
    corrigir_por_inflacao: bool = False


class TargetAllocationDTO(BaseModel):
    por_classe: dict[AssetClass, float]


class GoalDTO(BaseModel):
    valor_meta: float = Field(gt=0)
    prazo_anos: float = Field(gt=0)


class SimulationConfigDTO(BaseModel):
    n_cenarios: int = Field(default=10_000, gt=0)
    horizonte_anos: float = Field(default=30.0, gt=0)
    seed: int = Field(default=42, ge=0)
    inflacao_aa: float = 0.04
    rebalanceamento: RebalanceMode = RebalanceMode.ANUAL_AO_ALVO
    df_tstudent: float = Field(default=6.0, gt=2.0)


class SimulationRunRequest(BaseModel):
    portfolio_id: int
    config: SimulationConfigDTO = SimulationConfigDTO()
    premissas_juros: PremissasJurosDTO = PremissasJurosDTO()
    cashflow: CashFlowDTO | None = None
    target: TargetAllocationDTO | None = None
    goal: GoalDTO | None = None


# --------------------------- Saída: simulação -----------------------------
class SimulationRunResponse(BaseModel):
    id: int
    status: str
    resumo: dict


class ResultsOut(BaseModel):
    id: int
    resumo: dict
    funil: dict          # meses, amostra de trajetórias, bandas de percentis
    histograma: dict     # edges + counts dos patrimônios finais nominais
    correlacao: dict     # labels + matriz (correlação da renda variável)


class VaRCVaROut(BaseModel):
    nivel: float
    var: float
    cvar: float


class RiskAnalysisOut(BaseModel):
    id: int
    var_cvar: list[VaRCVaROut]
    prob_ruina: float
    prob_meta: float | None
    drawdown: dict
    contribuicao: dict


class StressOut(BaseModel):
    id: int
    comparacoes: list[dict]   # uma por preset: nome, descricao, resumo {metric: [base, stress]}


# --------------------------- Fase 6: insights / rebalance / aposentadoria -----
class InsightsOut(BaseModel):
    id: int
    insights: list[dict]   # categoria, severidade, texto, metrica, valor


class RebalanceOut(BaseModel):
    id: int
    valor_total: float
    turnover: float
    por_classe: list[dict]
    trades: list[dict]


class RetirementRequest(BaseModel):
    idade_atual: float = Field(gt=0)
    idade_aposentadoria: float = Field(gt=0)
    idade_final: float = Field(gt=0)
    aporte_mensal: float = Field(default=0.0, ge=0)
    saque_mensal_desejado: float = Field(default=0.0, ge=0)
    alvo_sucesso: float = Field(default=0.90, gt=0, lt=1)


class RetirementOut(BaseModel):
    id: int
    prob_sucesso: float
    saque_desejado: float
    saque_sustentavel: float
    alvo_sucesso: float
    patrimonio_aposentadoria: dict
    patrimonio_final: dict
    meses_acumulacao: int
    meses_total: int
