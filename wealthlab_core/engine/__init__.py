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
from wealthlab_core.engine.metrics import (
    ContribuicaoRisco,
    Drawdown,
    RiskAnalysis,
    VaRCVaR,
    analisar_risco,
    contribuicao_ao_risco,
    estatisticas_drawdown,
    matriz_covariancia_anual,
    max_drawdown_por_trajetoria,
    pesos_iniciais,
    prob_meta,
    prob_ruina,
    simular_retornos_1ano,
    var_cvar,
)
from wealthlab_core.engine.stress import (
    PRESETS,
    StressComparison,
    StressScenario,
    aplicar_correlacao_alvo,
    comparar_base_vs_stress,
    estressar_juros,
    estressar_parametros,
    precos_com_haircut,
    rodar_cenario_stress,
)
from wealthlab_core.engine.insights import Insight, gerar_insights
from wealthlab_core.engine.rebalance import (
    DeltaClasse,
    RebalanceRecommendation,
    Trade,
    recomendar_rebalanceamento,
)
from wealthlab_core.engine.retirement import RetirementResult, analisar_aposentadoria

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
    "VaRCVaR",
    "Drawdown",
    "ContribuicaoRisco",
    "RiskAnalysis",
    "var_cvar",
    "simular_retornos_1ano",
    "prob_ruina",
    "prob_meta",
    "max_drawdown_por_trajetoria",
    "estatisticas_drawdown",
    "pesos_iniciais",
    "matriz_covariancia_anual",
    "contribuicao_ao_risco",
    "analisar_risco",
    "StressScenario",
    "StressComparison",
    "PRESETS",
    "aplicar_correlacao_alvo",
    "estressar_parametros",
    "estressar_juros",
    "precos_com_haircut",
    "rodar_cenario_stress",
    "comparar_base_vs_stress",
    "Insight",
    "gerar_insights",
    "DeltaClasse",
    "Trade",
    "RebalanceRecommendation",
    "recomendar_rebalanceamento",
    "RetirementResult",
    "analisar_aposentadoria",
]
