"""Stress testing por parâmetros chocados (Fase 3).

Filosofia (decidida na spec): NÃO é replay histórico. Um cenário de stress é um
conjunto de *overrides* aplicado aos parâmetros do modelo, produzindo um regime
adverso estilizado:

  - drift↓        : a deriva esperada cai (μ_log_aa + Δ, com Δ ≤ 0).
  - vol↑          : a volatilidade sobe (σ × multiplicador).
  - correlações→1 : as correlações convergem para 1 (mistura com a matriz de uns).
                    Isto captura o que a correlação ESTÁTICA esconde — em crise,
                    a diversificação evapora porque "tudo cai junto".
  - choque de juros no IPCA+ : hit instantâneo de marcação a mercado nos papéis
                    IPCA+ via duration: ΔP/P ≈ −duration·Δy.
  - (opcional) deslocamento de Selic/IPCA projetados.

Presets nomeados (2008, COVID-2020, Estagflação, Brasil-2015) são CHOQUES
ESTILIZADOS, não reproduções exatas. Servem para comparação Base vs. Stress.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wealthlab_core.domain.assets import Portfolio
from wealthlab_core.domain.config import PASSOS_POR_ANO, SimulationConfig
from wealthlab_core.domain.enums import AssetClass
from wealthlab_core.domain.plan import CashFlowPlan, TargetAllocation
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.metrics import (
    estatisticas_drawdown,
    prob_ruina,
    simular_retornos_1ano,
    var_cvar,
)
from wealthlab_core.engine.simulator import SimulationResult, simular_portfolio
from wealthlab_core.utils import get_logger

logger = get_logger("wealthlab_core.engine.stress")


# ---------------------------------------------------------------------------
# Definição de um cenário de stress
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StressScenario:
    """Conjunto de overrides que define um regime adverso estilizado.

    Os defaults são NEUTROS: um `StressScenario(nome="neutro")` não altera nada,
    o que é útil como caso-base e para testes de identidade.
    """

    nome: str
    delta_drift_aa: float = 0.0          # somado à deriva log anual (≤0 = pior)
    vol_multiplicador: float = 1.0       # multiplica a volatilidade (>1 = pior)
    intensidade_correlacao: float = 0.0  # λ em [0,1]; 1 = correlações→1
    choque_juros_ipca_aa: float = 0.0    # Δy aplicado ao IPCA+ (>0 = alta = queda de preço)
    delta_selic_aa: float = 0.0          # desloca a Selic projetada
    delta_ipca_aa: float = 0.0           # desloca o IPCA projetado
    descricao: str = ""

    def haircut_ipca(self, duration_anos: float) -> float:
        """Fator de preço do papel IPCA+ após o choque: (1 − duration·Δy).

        Aproximação linear de 1ª ordem (válida para Δy pequeno). Limitada a 0
        para não gerar preço negativo em choques extremos.
        """
        return max(1.0 - duration_anos * self.choque_juros_ipca_aa, 0.0)


def aplicar_correlacao_alvo(corr: np.ndarray, intensidade: float) -> np.ndarray:
    """Empurra a matriz de correlação em direção a 1 (mistura convexa).

        corr_stress = (1−λ)·corr + λ·J,   J = matriz de uns, diagonal mantida 1.

    Como J é PSD e corr é PD, a combinação é PD para λ<1; em λ=1 vira singular
    (rank 1), então aplicamos um *shrink* mínimo para garantir Cholesky.
    """
    intensidade = float(np.clip(intensidade, 0.0, 1.0))
    n = corr.shape[0]
    J = np.ones((n, n))
    corr_stress = (1.0 - intensidade) * corr + intensidade * J
    np.fill_diagonal(corr_stress, 1.0)

    # Shrink mínimo em direção à identidade -> garante positiva-definida mesmo
    # quando intensidade=1 (correlações praticamente 1, mas Cholesky funciona).
    eps = 1e-8
    corr_stress = (1.0 - eps) * corr_stress + eps * np.eye(n)
    np.fill_diagonal(corr_stress, 1.0)
    return corr_stress


def estressar_parametros(
    params: EstimatedParams,
    scenario: StressScenario,
) -> EstimatedParams:
    """Aplica os overrides de RV (drift, vol, correlação) e devolve novos params."""
    sigma_aa = params.sigma_aa * scenario.vol_multiplicador
    corr = aplicar_correlacao_alvo(params.corr, scenario.intensidade_correlacao)

    # Reconstrói a covariância anual a partir de σ e da correlação chocados.
    D = np.diag(sigma_aa)
    cov_aa = D @ corr @ D

    mu_log_aa = params.mu_log_aa + scenario.delta_drift_aa

    return EstimatedParams(
        tickers=list(params.tickers),
        mu_log_mensal=mu_log_aa / PASSOS_POR_ANO,
        cov_mensal=cov_aa / PASSOS_POR_ANO,
        mu_log_aa=mu_log_aa,
        sigma_aa=sigma_aa,
        corr=corr,
    )


def estressar_juros(premissas: PremissasJuros, scenario: StressScenario) -> PremissasJuros:
    """Desloca Selic/IPCA projetados conforme o cenário."""
    return PremissasJuros(
        selic_aa=premissas.selic_aa + scenario.delta_selic_aa,
        ipca_aa=premissas.ipca_aa + scenario.delta_ipca_aa,
    )


def precos_com_haircut(
    portfolio: Portfolio,
    scenario: StressScenario,
    precos_iniciais: dict[str, float] | None = None,
) -> dict[str, float]:
    """Aplica o hit de marcação a mercado aos papéis IPCA+ (via duration).

    Retorna um novo dicionário de preços; tickers não-IPCA+ ficam inalterados.
    """
    precos = dict(precos_iniciais or {})
    for h in portfolio.holdings:
        a = h.asset
        if a.classe == AssetClass.FIXED_INCOME_IPCA and a.fixed_income_terms is not None:
            dur = a.fixed_income_terms.duration_anos
            base = precos.get(a.ticker, 1.0)
            precos[a.ticker] = base * scenario.haircut_ipca(dur)
    return precos


def rodar_cenario_stress(
    portfolio: Portfolio,
    config: SimulationConfig,
    premissas_juros: PremissasJuros,
    scenario: StressScenario,
    params_rv: EstimatedParams | None = None,
    cashflow: CashFlowPlan | None = None,
    target: TargetAllocation | None = None,
    precos_iniciais: dict[str, float] | None = None,
) -> SimulationResult:
    """Roda a simulação completa sob um cenário de stress."""
    params_s = estressar_parametros(params_rv, scenario) if params_rv is not None else None
    juros_s = estressar_juros(premissas_juros, scenario)
    precos_s = precos_com_haircut(portfolio, scenario, precos_iniciais)
    logger.info("rodando stress '%s'", scenario.nome)
    return simular_portfolio(
        portfolio, config, juros_s,
        params_rv=params_s, cashflow=cashflow, target=target, precos_iniciais=precos_s,
    )


# ---------------------------------------------------------------------------
# Comparação Base vs. Stress
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StressComparison:
    """Resultado lado a lado Base vs. Stress.

    `resumo` mapeia cada métrica -> (valor_base, valor_stress).
    """

    nome: str
    base: SimulationResult
    stress: SimulationResult
    resumo: dict[str, tuple[float, float]]

    def tabela(self) -> list[tuple[str, float, float]]:
        """Linhas (métrica, base, stress) para exibição."""
        return [(k, v[0], v[1]) for k, v in self.resumo.items()]


def _resumo_metrico(result: SimulationResult, ret_1ano: np.ndarray) -> dict[str, float]:
    p10, p50, p90 = np.percentile(result.patrimonio_final, [10, 50, 90])
    vc = var_cvar(ret_1ano, niveis=(0.95,))[0.95]
    dd = estatisticas_drawdown(result.trajetorias_nominais)
    return {
        "p10_final": float(p10),
        "p50_final": float(p50),
        "p90_final": float(p90),
        "prob_ruina": prob_ruina(result),
        "drawdown_pior": dd.pior,
        "var_95_1ano": vc.var,
        "cvar_95_1ano": vc.cvar,
    }


def comparar_base_vs_stress(
    portfolio: Portfolio,
    config: SimulationConfig,
    premissas_juros: PremissasJuros,
    scenario: StressScenario,
    params_rv: EstimatedParams | None = None,
    cashflow: CashFlowPlan | None = None,
    target: TargetAllocation | None = None,
    precos_iniciais: dict[str, float] | None = None,
) -> StressComparison:
    """Compara a carteira no regime base e sob o cenário de stress.

    Base e stress compartilham a mesma seed (via `config`), então as diferenças
    refletem só os parâmetros chocados — não o sorteio.
    """
    # --- Base ---
    base = simular_portfolio(
        portfolio, config, premissas_juros,
        params_rv=params_rv, cashflow=cashflow, target=target,
        precos_iniciais=precos_iniciais,
    )
    base_ret1 = simular_retornos_1ano(
        portfolio, config, premissas_juros, params_rv=params_rv,
        precos_iniciais=precos_iniciais,
    )
    resumo_base = _resumo_metrico(base, base_ret1)

    # --- Stress ---
    params_s = estressar_parametros(params_rv, scenario) if params_rv is not None else None
    juros_s = estressar_juros(premissas_juros, scenario)
    precos_s = precos_com_haircut(portfolio, scenario, precos_iniciais)

    stress = simular_portfolio(
        portfolio, config, juros_s,
        params_rv=params_s, cashflow=cashflow, target=target, precos_iniciais=precos_s,
    )
    stress_ret1 = simular_retornos_1ano(
        portfolio, config, juros_s, params_rv=params_s, precos_iniciais=precos_s,
    )
    resumo_stress = _resumo_metrico(stress, stress_ret1)

    resumo = {k: (resumo_base[k], resumo_stress[k]) for k in resumo_base}
    return StressComparison(nome=scenario.nome, base=base, stress=stress, resumo=resumo)


# ---------------------------------------------------------------------------
# Presets — CHOQUES ESTILIZADOS (não são replays exatos)
# ---------------------------------------------------------------------------
PRESETS: dict[str, StressScenario] = {
    "2008": StressScenario(
        nome="2008",
        descricao="Crise financeira global (estilizada): colapso de ações, vol dobra, "
        "correlações disparam, fuga para qualidade derruba juros.",
        delta_drift_aa=-0.25,
        vol_multiplicador=2.0,
        intensidade_correlacao=0.90,
        choque_juros_ipca_aa=0.015,
        delta_selic_aa=-0.02,
        delta_ipca_aa=-0.01,
    ),
    "COVID-2020": StressScenario(
        nome="COVID-2020",
        descricao="Choque pandêmico (estilizado): queda abrupta e severa, vol e "
        "correlações no extremo, cortes de juros.",
        delta_drift_aa=-0.30,
        vol_multiplicador=2.5,
        intensidade_correlacao=0.95,
        choque_juros_ipca_aa=0.01,
        delta_selic_aa=-0.03,
        delta_ipca_aa=-0.01,
    ),
    "Estagflacao": StressScenario(
        nome="Estagflacao",
        descricao="Estagflação (estilizada): crescimento fraco com inflação alta, "
        "juros sobem e marcam a mercado o IPCA+.",
        delta_drift_aa=-0.15,
        vol_multiplicador=1.6,
        intensidade_correlacao=0.75,
        choque_juros_ipca_aa=0.03,
        delta_selic_aa=0.05,
        delta_ipca_aa=0.06,
    ),
    "Brasil-2015": StressScenario(
        nome="Brasil-2015",
        descricao="Crise doméstica (estilizada): recessão + inflação + alta de juros; "
        "ações caem e o IPCA+ sofre marcação.",
        delta_drift_aa=-0.20,
        vol_multiplicador=1.8,
        intensidade_correlacao=0.80,
        choque_juros_ipca_aa=0.04,
        delta_selic_aa=0.06,
        delta_ipca_aa=0.05,
    ),
}
