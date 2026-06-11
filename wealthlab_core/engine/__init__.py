"""Motor quantitativo: estimação, geração de retornos, renda fixa e simulação."""

from wealthlab_core.engine.estimation import EstimatedParams, estimar_parametros
from wealthlab_core.engine.fixed_income import (
    PremissasJuros,
    fator_mensal_constante,
    gerar_fatores_rf,
    taxa_anual_carrego,
)
from wealthlab_core.engine.returns import (
    gerar_choques_tstudent,
    gerar_log_retornos_rv,
)
from wealthlab_core.engine.simulator import (
    SimulationResult,
    simular_portfolio,
)

__all__ = [
    "EstimatedParams",
    "estimar_parametros",
    "PremissasJuros",
    "taxa_anual_carrego",
    "fator_mensal_constante",
    "gerar_fatores_rf",
    "gerar_choques_tstudent",
    "gerar_log_retornos_rv",
    "SimulationResult",
    "simular_portfolio",
]
