"""Modelo de domínio (Pydantic) do WealthLab Core."""

from wealthlab_core.domain.assets import Asset, Holding, Portfolio
from wealthlab_core.domain.config import PASSOS_POR_ANO, SimulationConfig
from wealthlab_core.domain.enums import (
    CLASSES_RENDA_FIXA,
    CLASSES_RENDA_VARIAVEL,
    AssetClass,
    Indexador,
    RebalanceMode,
)
from wealthlab_core.domain.fixed_income import FixedIncomeTerms
from wealthlab_core.domain.plan import CashFlowPlan, FinancialGoal, TargetAllocation

__all__ = [
    "Asset",
    "Holding",
    "Portfolio",
    "AssetClass",
    "Indexador",
    "RebalanceMode",
    "CLASSES_RENDA_FIXA",
    "CLASSES_RENDA_VARIAVEL",
    "FixedIncomeTerms",
    "CashFlowPlan",
    "TargetAllocation",
    "FinancialGoal",
    "SimulationConfig",
    "PASSOS_POR_ANO",
]
