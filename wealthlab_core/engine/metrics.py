"""Métricas de risco (Fase 2).

Cinco famílias de métricas, com bases distintas — e é importante não confundi-las:

  - VaR / CVaR (95% e 99%): risco de MERCADO sobre a distribuição do RETORNO da
    carteira em 1 ANO, com os pesos atuais, em buy-and-hold e SEM fluxos. Mede
    "quanto posso perder num ano ruim", isolando o mercado dos aportes/saques.

  - Probabilidade de ruína: fração de trajetórias que tocam zero em QUALQUER
    ponto até o horizonte total (usa a simulação completa, com fluxos e
    rebalanceamento). É um conceito de horizonte longo — distinto do VaR.

  - Probabilidade de meta: fração de trajetórias com patrimônio ≥ meta no prazo.

  - Drawdown máximo: maior queda pico-a-vale do patrimônio em cada trajetória;
    reportamos média, mediana e pior caso.

  - Contribuição ao risco: decomposição da variância da carteira por ativo/classe
    (marginal contribution to risk). Renda fixa, sendo determinística no base,
    aparece com ~0% — o risco se concentra na renda variável/cripto.

Convenção de sinal de VaR/CVaR: reportados como PERDA POSITIVA (ex.: VaR=0.20
significa "perda de 20%"). Valor negativo significaria ganho mesmo no pior
quantil (sem perda).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wealthlab_core.domain.assets import Portfolio
from wealthlab_core.domain.config import PASSOS_POR_ANO, SimulationConfig
from wealthlab_core.domain.enums import (
    CLASSES_RENDA_FIXA,
    CLASSES_RENDA_VARIAVEL,
    AssetClass,
)
from wealthlab_core.domain.plan import CashFlowPlan, FinancialGoal, TargetAllocation
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros, gerar_fatores_rf
from wealthlab_core.engine.returns import gerar_log_retornos_rv
from wealthlab_core.engine.simulator import SimulationResult, simular_portfolio
from wealthlab_core.utils import get_logger

logger = get_logger("wealthlab_core.engine.metrics")


# ---------------------------------------------------------------------------
# Dataclasses de saída
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class VaRCVaR:
    """VaR e CVaR num nível de confiança (perdas como fração positiva)."""

    nivel: float        # ex.: 0.95
    var: float          # perda no quantil (1-nível); positivo = perda
    cvar: float         # Expected Shortfall: perda média na cauda além do VaR


@dataclass(frozen=True)
class Drawdown:
    """Estatísticas de drawdown máximo entre trajetórias (frações positivas)."""

    medio: float
    mediano: float
    pior: float


@dataclass(frozen=True)
class ContribuicaoRisco:
    """Decomposição do risco (volatilidade anual) da carteira.

    `pctr` (percent contribution to risk) soma 1 sobre os ativos; `contrib_vol`
    é a parcela em pontos de volatilidade anual (soma = vol_anual_carteira).
    """

    ordem: list[str]
    pctr: np.ndarray                 # (n,) fração da variância; soma 1
    contrib_vol: np.ndarray          # (n,) parcela da vol anual; soma = vol total
    vol_anual_carteira: float
    por_classe: dict[AssetClass, float]   # PCTR agregado por classe (soma 1)

    def ranking(self) -> list[tuple[str, float]]:
        """Ativos ordenados por contribuição decrescente ao risco."""
        pares = list(zip(self.ordem, self.pctr))
        return sorted(pares, key=lambda x: x[1], reverse=True)


@dataclass(frozen=True)
class RiskAnalysis:
    """Pacote completo de métricas — mapeia para GET /simulation/{id}/risk-analysis."""

    var_cvar: dict[float, VaRCVaR]
    prob_ruina: float
    prob_meta: float | None
    drawdown: Drawdown
    contribuicao: ContribuicaoRisco


# ---------------------------------------------------------------------------
# VaR / CVaR
# ---------------------------------------------------------------------------
def var_cvar(
    retornos: np.ndarray,
    niveis: tuple[float, ...] = (0.95, 0.99),
) -> dict[float, VaRCVaR]:
    """VaR e CVaR (Expected Shortfall) de um array de retornos.

    Para nível α, o VaR é a perda no quantil (1−α) e o CVaR é a perda MÉDIA
    condicionada a estar além desse quantil (a cauda esquerda).
    """
    retornos = np.asarray(retornos, dtype=float)
    out: dict[float, VaRCVaR] = {}
    for nivel in niveis:
        q = np.percentile(retornos, (1.0 - nivel) * 100.0)   # quantil da perda
        cauda = retornos[retornos <= q]
        cvar = -cauda.mean() if cauda.size > 0 else -q
        out[nivel] = VaRCVaR(nivel=nivel, var=float(-q), cvar=float(cvar))
    return out


def simular_retornos_1ano(
    portfolio: Portfolio,
    config: SimulationConfig,
    premissas_juros: PremissasJuros,
    params_rv: EstimatedParams | None = None,
    precos_iniciais: dict[str, float] | None = None,
    n_cenarios: int | None = None,
    seed: int | None = None,
) -> np.ndarray:
    """Distribuição do retorno da carteira em 1 ano (base do VaR/CVaR).

    Buy-and-hold com os pesos ATUAIS, 12 meses, SEM fluxos. RV via t-Student;
    RF via carrego determinístico. Retorna (n_cenarios,) de retornos aritméticos.
    """
    n_cen = n_cenarios or config.n_cenarios
    # Seed distinta da simulação principal para não reusar exatamente os mesmos
    # choques (a análise de risco é um experimento à parte, porém reprodutível).
    rng = np.random.default_rng((seed if seed is not None else config.seed) + 1)

    pesos, _ = pesos_iniciais(portfolio, precos_iniciais)
    assets = portfolio.assets
    n_ativos = len(assets)
    rv_idx = [i for i, a in enumerate(assets) if a.classe in CLASSES_RENDA_VARIAVEL]
    rf_idx = [i for i, a in enumerate(assets) if a.classe in CLASSES_RENDA_FIXA]

    fator_1ano = np.ones((n_cen, n_ativos), dtype=float)

    if rv_idx:
        if params_rv is None:
            raise ValueError("params_rv é obrigatório quando há renda variável.")
        p = params_rv.reordenar([assets[i].ticker for i in rv_idx])
        log_ret = gerar_log_retornos_rv(
            p.mu_log_mensal, p.cov_mensal, n_cen, PASSOS_POR_ANO, config.df_tstudent, rng
        )
        # Compõe 12 meses: fator anual = exp(soma dos log-retornos mensais).
        fator_1ano[:, rv_idx] = np.exp(log_ret.sum(axis=1))

    if rf_idx:
        fr = gerar_fatores_rf([assets[i] for i in rf_idx], premissas_juros)  # (n_rf,)
        fator_1ano[:, rf_idx] = (fr ** PASSOS_POR_ANO)[None, :]

    # Retorno da carteira buy-and-hold = soma ponderada dos fatores − 1.
    ret_carteira = (fator_1ano * pesos[None, :]).sum(axis=1) - 1.0
    return ret_carteira


# ---------------------------------------------------------------------------
# Ruína e meta (sobre a simulação completa)
# ---------------------------------------------------------------------------
def prob_ruina(result: SimulationResult) -> float:
    """Fração de trajetórias que tocaram zero antes do horizonte final."""
    return float(result.ruina_mask.mean())


def prob_meta(result: SimulationResult, goal: FinancialGoal) -> float:
    """Fração de trajetórias com patrimônio nominal ≥ meta no prazo da meta."""
    mes = int(round(goal.prazo_anos * PASSOS_POR_ANO))
    mes = min(mes, result.n_passos)   # não ultrapassa o horizonte simulado
    patrimonio_no_prazo = result.trajetorias_nominais[:, mes]
    return float((patrimonio_no_prazo >= goal.valor_meta).mean())


# ---------------------------------------------------------------------------
# Drawdown
# ---------------------------------------------------------------------------
def max_drawdown_por_trajetoria(trajetorias: np.ndarray) -> np.ndarray:
    """Drawdown máximo (fração) de cada trajetória.

    Drawdown = 1 − W_t / max(W_{≤t}). Usa o máximo acumulado (pico histórico)
    como referência. Vetorizado sobre os cenários.
    """
    pico = np.maximum.accumulate(trajetorias, axis=1)
    # Evita divisão por zero (pico só é 0 se o início for 0, fora do nosso caso).
    with np.errstate(divide="ignore", invalid="ignore"):
        queda = 1.0 - np.where(pico > 0, trajetorias / pico, 1.0)
    return queda.max(axis=1)


def estatisticas_drawdown(trajetorias: np.ndarray) -> Drawdown:
    dd = max_drawdown_por_trajetoria(trajetorias)
    return Drawdown(
        medio=float(dd.mean()),
        mediano=float(np.median(dd)),
        pior=float(dd.max()),
    )


# ---------------------------------------------------------------------------
# Contribuição ao risco (marginal contribution to risk)
# ---------------------------------------------------------------------------
def pesos_iniciais(
    portfolio: Portfolio,
    precos_iniciais: dict[str, float] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Pesos por valor inicial (R$) de cada posição; somam 1."""
    precos = precos_iniciais or {}
    valores = np.array(
        [h.quantidade * precos.get(h.asset.ticker, 1.0) for h in portfolio.holdings],
        dtype=float,
    )
    total = valores.sum()
    if total <= 0:
        raise ValueError("valor total da carteira deve ser positivo.")
    return valores / total, [h.asset.ticker for h in portfolio.holdings]


def matriz_covariancia_anual(
    portfolio: Portfolio,
    params_rv: EstimatedParams | None = None,
) -> np.ndarray:
    """Covariância anual de TODOS os ativos (ordem da carteira).

    Renda fixa tem variância/covariância 0 no modelo base (carrego
    determinístico) — por isso entra como zeros. Isso faz a RF contribuir ~0%
    para o risco, o que é exatamente o comportamento correto do modelo.
    """
    assets = portfolio.assets
    n = len(assets)
    cov = np.zeros((n, n), dtype=float)
    rv_idx = [i for i, a in enumerate(assets) if a.classe in CLASSES_RENDA_VARIAVEL]
    if rv_idx:
        if params_rv is None:
            raise ValueError("params_rv é obrigatório quando há renda variável.")
        p = params_rv.reordenar([assets[i].ticker for i in rv_idx])
        cov_rv_aa = p.cov_mensal * PASSOS_POR_ANO   # anualiza
        cov[np.ix_(rv_idx, rv_idx)] = cov_rv_aa
    return cov


def contribuicao_ao_risco(
    cov_anual: np.ndarray,
    pesos: np.ndarray,
    ordem: list[str],
    classes: list[AssetClass],
) -> ContribuicaoRisco:
    """Decompõe a volatilidade anual da carteira por ativo e por classe.

    Matemática (marginal contribution to risk):
        σ_p² = wᵀ Σ w                          (variância da carteira)
        contribuição do ativo i à variância = w_i · (Σ w)_i   (somam σ_p²)
        PCTR_i = w_i (Σw)_i / σ_p²             (fração; soma 1)
        contribuição à vol = w_i (Σw)_i / σ_p  (somam σ_p)
    A identidade w_i(Σw)_i somar σ_p² é o teorema de Euler aplicado à função
    homogênea de grau 2 que é a variância.
    """
    pesos = np.asarray(pesos, dtype=float)
    sigma_w = cov_anual @ pesos
    var_p = float(pesos @ sigma_w)
    vol_p = float(np.sqrt(var_p)) if var_p > 0 else 0.0

    if var_p <= 0:
        # Carteira sem risco de mercado (ex.: 100% renda fixa).
        pctr = np.zeros_like(pesos)
        contrib_vol = np.zeros_like(pesos)
    else:
        contrib_var = pesos * sigma_w        # somam var_p
        pctr = contrib_var / var_p           # somam 1
        contrib_vol = contrib_var / vol_p    # somam vol_p

    por_classe: dict[AssetClass, float] = {}
    for c, p in zip(classes, pctr):
        por_classe[c] = por_classe.get(c, 0.0) + float(p)

    return ContribuicaoRisco(
        ordem=list(ordem),
        pctr=pctr,
        contrib_vol=contrib_vol,
        vol_anual_carteira=vol_p,
        por_classe=por_classe,
    )


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
def analisar_risco(
    portfolio: Portfolio,
    config: SimulationConfig,
    premissas_juros: PremissasJuros,
    params_rv: EstimatedParams | None = None,
    cashflow: CashFlowPlan | None = None,
    target: TargetAllocation | None = None,
    precos_iniciais: dict[str, float] | None = None,
    goal: FinancialGoal | None = None,
    niveis: tuple[float, ...] = (0.95, 0.99),
    result: SimulationResult | None = None,
) -> RiskAnalysis:
    """Calcula o pacote completo de métricas.

    Reusa um `SimulationResult` se fornecido (para ruína/meta/drawdown);
    caso contrário roda a simulação completa internamente.
    """
    if result is None:
        result = simular_portfolio(
            portfolio, config, premissas_juros,
            params_rv=params_rv, cashflow=cashflow, target=target,
            precos_iniciais=precos_iniciais,
        )

    # VaR/CVaR — base de 1 ano, sem fluxos, pesos atuais.
    ret_1ano = simular_retornos_1ano(
        portfolio, config, premissas_juros, params_rv=params_rv,
        precos_iniciais=precos_iniciais,
    )
    vc = var_cvar(ret_1ano, niveis)

    # Contribuição ao risco — covariância anual + pesos atuais.
    pesos, ordem = pesos_iniciais(portfolio, precos_iniciais)
    cov = matriz_covariancia_anual(portfolio, params_rv)
    classes = [a.classe for a in portfolio.assets]
    contrib = contribuicao_ao_risco(cov, pesos, ordem, classes)

    return RiskAnalysis(
        var_cvar=vc,
        prob_ruina=prob_ruina(result),
        prob_meta=(prob_meta(result, goal) if goal is not None else None),
        drawdown=estatisticas_drawdown(result.trajetorias_nominais),
        contribuicao=contrib,
    )
