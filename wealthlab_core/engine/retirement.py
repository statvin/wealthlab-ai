"""Módulo de aposentadoria — reusa o motor em duas fases.

Modela ACUMULAÇÃO (aportes até a aposentadoria) seguida de DECUMULAÇÃO (saques
até a idade final), usando o `net_fluxo` customizado do simulador.

Responde "posso me aposentar aos X?":
  - probabilidade de sucesso (o dinheiro durar até a idade final);
  - patrimônio esperado no momento da aposentadoria;
  - saque mensal SUSTENTÁVEL (maior saque com sucesso ≥ alvo), via busca binária.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wealthlab_core.domain.assets import Portfolio
from wealthlab_core.domain.config import SimulationConfig
from wealthlab_core.domain.plan import TargetAllocation
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.metrics import prob_ruina
from wealthlab_core.engine.simulator import simular_portfolio


@dataclass(frozen=True)
class RetirementResult:
    prob_sucesso: float                       # para o saque desejado
    saque_desejado: float
    saque_sustentavel: float                  # maior saque com sucesso ≥ alvo
    alvo_sucesso: float
    patrimonio_aposentadoria: dict[str, float]  # percentis no momento da aposentadoria
    patrimonio_final: dict[str, float]          # percentis na idade final
    meses_acumulacao: int
    meses_total: int


def _percentis(arr: np.ndarray, qs: tuple[int, ...] = (10, 50, 90)) -> dict[str, float]:
    p = np.percentile(arr, qs)
    return {f"p{int(q)}": float(v) for q, v in zip(qs, p)}


def analisar_aposentadoria(
    portfolio: Portfolio,
    config: SimulationConfig,
    premissas_juros: PremissasJuros,
    *,
    idade_atual: float,
    idade_aposentadoria: float,
    idade_final: float,
    aporte_mensal: float,
    saque_mensal_desejado: float,
    params_rv: EstimatedParams | None = None,
    target: TargetAllocation | None = None,
    precos_iniciais: dict[str, float] | None = None,
    alvo_sucesso: float = 0.90,
    n_cenarios_busca: int = 2000,
    iteracoes_busca: int = 14,
) -> RetirementResult:
    if not (idade_atual < idade_aposentadoria <= idade_final):
        raise ValueError("exige idade_atual < idade_aposentadoria <= idade_final.")

    anos_total = idade_final - idade_atual
    cfg_cheio = config.model_copy(update={"horizonte_anos": anos_total})
    n_passos = cfg_cheio.n_passos
    meses_acum = min(int(round((idade_aposentadoria - idade_atual) * 12)), n_passos)

    def net_fluxo(saque: float) -> np.ndarray:
        nf = np.empty(n_passos, dtype=float)
        nf[:meses_acum] = aporte_mensal      # fase de acumulação
        nf[meses_acum:] = -saque             # fase de decumulação
        return nf

    def rodar(saque: float, n_cen: int):
        cfg = config.model_copy(update={"horizonte_anos": anos_total, "n_cenarios": n_cen})
        return simular_portfolio(
            portfolio, cfg, premissas_juros, params_rv=params_rv, target=target,
            precos_iniciais=precos_iniciais, net_fluxo=net_fluxo(saque),
        )

    def sucesso(saque: float, n_cen: int) -> float:
        return 1.0 - prob_ruina(rodar(saque, n_cen))

    # Run completo para o saque desejado (métricas reportadas).
    res = rodar(saque_mensal_desejado, config.n_cenarios)
    prob_sucesso = 1.0 - prob_ruina(res)
    patr_apos = _percentis(res.trajetorias_nominais[:, meses_acum])
    patr_final = _percentis(res.patrimonio_final)

    # Busca binária do saque sustentável (sucesso é monótono decrescente no saque;
    # mesma seed em todos os runs garante monotonicidade limpa).
    lo, hi = 0.0, max(patr_apos["p50"] * 0.01, saque_mensal_desejado * 2, 1.0)
    for _ in range(8):  # garante que `hi` é insustentável
        if sucesso(hi, n_cenarios_busca) < alvo_sucesso:
            break
        hi *= 2
    for _ in range(iteracoes_busca):
        mid = (lo + hi) / 2
        if sucesso(mid, n_cenarios_busca) >= alvo_sucesso:
            lo = mid
        else:
            hi = mid
    saque_sustentavel = lo

    return RetirementResult(
        prob_sucesso=prob_sucesso,
        saque_desejado=saque_mensal_desejado,
        saque_sustentavel=saque_sustentavel,
        alvo_sucesso=alvo_sucesso,
        patrimonio_aposentadoria=patr_apos,
        patrimonio_final=patr_final,
        meses_acumulacao=meses_acum,
        meses_total=n_passos,
    )
