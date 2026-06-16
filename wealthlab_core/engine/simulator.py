"""Motor de simulação: evolução do patrimônio (Monte Carlo).

Aqui vivem as DUAS camadas de vetorização da spec:

  CAMADA 1 (em returns.py / fixed_income.py): geração de TODOS os retornos de uma
  vez, sem loop sobre cenários.

  CAMADA 2 (aqui, `_evoluir_patrimonio`): um único loop sobre os ~360 passos de
  tempo, VETORIZADO sobre os cenários. É inevitável porque o patrimônio é
  recursivo e os fluxos são aditivos:
        W_t = (W_{t-1} + aporte_t − saque_t) · (1 + retorno_t)
  Fluxos aditivos quebram o `cumprod`, então não dá para fechar em forma
  fechada — mas o loop é sobre o tempo (curto), não sobre cenários (enorme).

PROIBIDO: `for cenario in cenarios:`. Cada operação dentro do loop opera no eixo
dos cenários de uma vez (arrays NumPy (n_cenarios, n_ativos)).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from wealthlab_core.domain.assets import Portfolio
from wealthlab_core.domain.config import PASSOS_POR_ANO, SimulationConfig
from wealthlab_core.domain.enums import (
    CLASSES_RENDA_FIXA,
    CLASSES_RENDA_VARIAVEL,
    RebalanceMode,
)
from wealthlab_core.domain.plan import CashFlowPlan, TargetAllocation
from wealthlab_core.engine.estimation import EstimatedParams
from wealthlab_core.engine.fixed_income import PremissasJuros, gerar_fatores_rf
from wealthlab_core.engine.returns import gerar_log_retornos_rv
from wealthlab_core.utils import get_logger

logger = get_logger("wealthlab_core.engine.simulator")


@dataclass
class SimulationResult:
    """Resultado de uma simulação.

    `trajetorias_nominais`: (n_cenarios, n_passos+1) — patrimônio total por passo,
    incluindo t=0. `valores_finais_por_ativo`: (n_cenarios, n_ativos) — útil para
    contribuição ao risco (Fase 2). `ruina_mask`: cenários que tocaram zero.
    """

    trajetorias_nominais: np.ndarray
    valores_finais_por_ativo: np.ndarray
    ordem_ativos: list[str]
    ruina_mask: np.ndarray
    config: SimulationConfig

    @property
    def n_cenarios(self) -> int:
        return self.trajetorias_nominais.shape[0]

    @property
    def n_passos(self) -> int:
        return self.trajetorias_nominais.shape[1] - 1

    @property
    def patrimonio_final(self) -> np.ndarray:
        """Patrimônio nominal no último passo, por cenário (n_cenarios,)."""
        return self.trajetorias_nominais[:, -1]

    def trajetorias_reais(self) -> np.ndarray:
        """Trajetórias em termos reais (deflacionadas pela inflação do config)."""
        meses = np.arange(self.n_passos + 1)
        deflator = (1.0 + self.config.inflacao_aa) ** (meses / PASSOS_POR_ANO)
        return self.trajetorias_nominais / deflator[None, :]

    def percentis_finais(self, qs: list[float], real: bool = False) -> np.ndarray:
        """Percentis do patrimônio final. `qs` em [0, 100]."""
        base = self.trajetorias_reais()[:, -1] if real else self.patrimonio_final
        return np.percentile(base, qs)


# ---------------------------------------------------------------------------
# Camada 2: evolução recursiva do patrimônio (loop em passos, vetor em cenários)
# ---------------------------------------------------------------------------
def _evoluir_patrimonio(
    valor_inicial: np.ndarray,       # (n_ativos,)
    fatores: np.ndarray,             # (n_cenarios, n_passos, n_ativos)
    net_fluxo: np.ndarray,           # (n_passos,) aporte − saque por passo
    onehot: np.ndarray,              # (n_ativos, n_classes)
    alvo_por_ativo: np.ndarray | None,   # (n_ativos,) peso-alvo da classe do ativo
    dist_default: np.ndarray,        # (n_ativos,) distribuição p/ aporte sem base
    fallback_share: np.ndarray,      # (n_ativos,) 1/qtd_na_classe (rebalance)
    rebalancear: bool,
    passos_por_ano: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n_cen, n_passos, n_ativos = fatores.shape

    V = np.broadcast_to(valor_inicial, (n_cen, n_ativos)).astype(float).copy()
    trajetoria = np.empty((n_cen, n_passos + 1), dtype=float)
    trajetoria[:, 0] = V.sum(axis=1)
    ruina = np.zeros(n_cen, dtype=bool)

    for t in range(n_passos):
        net = float(net_fluxo[t])

        # (a) Fluxo de caixa no início do passo (aditivo).
        if net != 0.0:
            W = V.sum(axis=1)                          # (n_cen,)
            tem_valor = W > 0.0
            # Distribui o fluxo proporcional aos pesos atuais (não rebalanceia).
            # Onde a carteira zerou, usa a distribuição default (permite que um
            # novo aporte "ressuscite" a carteira de forma controlada).
            denom = np.where(tem_valor, W, 1.0)[:, None]
            pesos = np.where(tem_valor[:, None], V / denom, dist_default[None, :])
            W_novo = np.clip(W + net, a_min=0.0, a_max=None)
            ruina |= (W + net) <= 0.0                  # tocou/passou zero = ruína
            V = pesos * W_novo[:, None]

        # (b) Retorno do passo — vetorizado sobre os cenários.
        V = V * fatores[:, t, :]

        # (c) Rebalanceamento anual ao alvo (a cada 12 passos).
        if rebalancear and ((t + 1) % passos_por_ano == 0):
            W = V.sum(axis=1)                          # (n_cen,)
            ativo = W > 0.0
            valor_classe = V @ onehot                  # (n_cen, n_classes)
            valor_classe_por_ativo = valor_classe @ onehot.T   # (n_cen, n_ativos)
            tem_classe = valor_classe_por_ativo > 0.0
            share = np.where(
                tem_classe,
                V / np.where(tem_classe, valor_classe_por_ativo, 1.0),
                fallback_share[None, :],
            )
            V_reb = (W[:, None] * alvo_por_ativo[None, :]) * share
            V = np.where(ativo[:, None], V_reb, V)

        trajetoria[:, t + 1] = V.sum(axis=1)

    return trajetoria, V, ruina


# ---------------------------------------------------------------------------
# Construção dos fluxos de caixa por passo
# ---------------------------------------------------------------------------
def _montar_fluxos(
    cashflow: CashFlowPlan | None,
    n_passos: int,
    inflacao_aa: float,
) -> np.ndarray:
    """Vetor (n_passos,) com aporte − saque por passo, respeitando a janela e o
    flag de correção pela inflação."""
    if cashflow is None:
        return np.zeros(n_passos, dtype=float)

    t = np.arange(n_passos)
    fim = cashflow.fim_mes if cashflow.fim_mes is not None else n_passos - 1
    na_janela = (t >= cashflow.inicio_mes) & (t <= fim)

    if cashflow.corrigir_por_inflacao:
        infl_m = (1.0 + inflacao_aa) ** (1.0 / PASSOS_POR_ANO) - 1.0
        fator_infl = (1.0 + infl_m) ** t
    else:
        fator_infl = np.ones(n_passos)

    aportes = np.where(na_janela, cashflow.aporte_mensal * fator_infl, 0.0)
    saques = np.where(na_janela, cashflow.saque_mensal * fator_infl, 0.0)
    return aportes - saques


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
def simular_portfolio(
    portfolio: Portfolio,
    config: SimulationConfig,
    premissas_juros: PremissasJuros,
    params_rv: EstimatedParams | None = None,
    cashflow: CashFlowPlan | None = None,
    target: TargetAllocation | None = None,
    precos_iniciais: dict[str, float] | None = None,
    net_fluxo: np.ndarray | None = None,
) -> SimulationResult:
    """Roda a simulação Monte Carlo para uma carteira.

    - `params_rv`: parâmetros estimados da renda variável (obrigatório se houver
      ativos de RV). É reordenado internamente para casar a ordem da carteira.
    - `premissas_juros`: cenário base de Selic/IPCA para a renda fixa.
    - `precos_iniciais`: preço unitário por ticker (default 1.0 → quantidade já é
      o valor em R$; conveniente para RF e para testes).
    - `net_fluxo`: opcional, vetor (n_passos,) de fluxo líquido (aporte − saque)
      por passo. Quando informado, substitui o derivado de `cashflow` — usado
      pela aposentadoria para modelar fases distintas (acumulação → decumulação).
    """
    t0 = time.perf_counter()

    assets = portfolio.assets
    n_ativos = len(assets)
    n_cen = config.n_cenarios
    n_passos = config.n_passos
    precos_iniciais = precos_iniciais or {}

    # Valor inicial em R$ por ativo.
    valor_inicial = np.array(
        [h.quantidade * precos_iniciais.get(h.asset.ticker, 1.0) for h in portfolio.holdings],
        dtype=float,
    )

    # Índices de renda variável e renda fixa (preservando a ordem da carteira).
    rv_idx = [i for i, a in enumerate(assets) if a.classe in CLASSES_RENDA_VARIAVEL]
    rf_idx = [i for i, a in enumerate(assets) if a.classe in CLASSES_RENDA_FIXA]

    rng = np.random.default_rng(config.seed)
    fatores = np.empty((n_cen, n_passos, n_ativos), dtype=float)

    # Bloco estocástico (renda variável): t-Student multivariada.
    if rv_idx:
        if params_rv is None:
            raise ValueError(
                "params_rv é obrigatório quando há ativos de renda variável."
            )
        rv_tickers = [assets[i].ticker for i in rv_idx]
        p = params_rv.reordenar(rv_tickers)
        log_ret = gerar_log_retornos_rv(
            p.mu_log_mensal, p.cov_mensal, n_cen, n_passos, config.df_tstudent, rng
        )
        fatores[:, :, rv_idx] = np.exp(log_ret)

    # Bloco de renda fixa: fatores mensais constantes, difundidos nos cenários.
    if rf_idx:
        assets_rf = [assets[i] for i in rf_idx]
        fr = gerar_fatores_rf(assets_rf, premissas_juros)   # (n_rf,)
        fatores[:, :, rf_idx] = fr[None, None, :]

    # Mapeamento de classes (one-hot) e estruturas de rebalanceamento.
    classes = [a.classe for a in assets]
    classes_unicas = list(dict.fromkeys(classes))   # únicas, preservando ordem
    col = {c: j for j, c in enumerate(classes_unicas)}
    onehot = np.zeros((n_ativos, len(classes_unicas)), dtype=float)
    for i, c in enumerate(classes):
        onehot[i, col[c]] = 1.0
    contagem = {c: classes.count(c) for c in classes_unicas}
    fallback_share = np.array([1.0 / contagem[c] for c in classes], dtype=float)

    rebalancear = config.rebalanceamento == RebalanceMode.ANUAL_AO_ALVO
    if rebalancear:
        if target is None:
            raise ValueError("rebalanceamento ANUAL_AO_ALVO exige um TargetAllocation.")
        if set(target.por_classe) != set(classes_unicas):
            raise ValueError(
                "as classes do TargetAllocation devem casar exatamente as classes "
                f"da carteira. Carteira={set(c.value for c in classes_unicas)}, "
                f"alvo={set(c.value for c in target.por_classe)}."
            )
        alvo_classe = np.array([target.por_classe[c] for c in classes_unicas])
        alvo_por_ativo = np.array([target.por_classe[c] for c in classes])
        dist_default = np.array(
            [target.por_classe[classes[i]] / contagem[classes[i]] for i in range(n_ativos)]
        )
    else:
        alvo_por_ativo = None
        dist_default = np.full(n_ativos, 1.0 / n_ativos)

    if net_fluxo is None:
        net_fluxo = _montar_fluxos(cashflow, n_passos, config.inflacao_aa)
    elif len(net_fluxo) != n_passos:
        raise ValueError(f"net_fluxo deve ter comprimento n_passos={n_passos}.")

    trajetoria, valores_finais, ruina = _evoluir_patrimonio(
        valor_inicial=valor_inicial,
        fatores=fatores,
        net_fluxo=net_fluxo,
        onehot=onehot,
        alvo_por_ativo=alvo_por_ativo,
        dist_default=dist_default,
        fallback_share=fallback_share,
        rebalancear=rebalancear,
        passos_por_ano=PASSOS_POR_ANO,
    )

    dt = time.perf_counter() - t0
    logger.info(
        "simulação: %d cenários × %d passos × %d ativos em %.2fs.",
        n_cen, n_passos, n_ativos, dt,
    )

    return SimulationResult(
        trajetorias_nominais=trajetoria,
        valores_finais_por_ativo=valores_finais,
        ordem_ativos=[a.ticker for a in assets],
        ruina_mask=ruina,
        config=config,
    )
