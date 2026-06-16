"""Recomendação de rebalanceamento da carteira REAL.

Dado um alvo desejado por classe, calcula quanto comprar/vender para chegar lá.

IMPORTANTE — não confundir com o rebalanceamento DENTRO da simulação
(RebalanceMode.ANUAL_AO_ALVO), que realoca as trajetórias ao longo do tempo.
Aqui é uma recomendação pontual sobre a carteira atual: "para sair da alocação
de hoje e chegar no alvo, faça estas compras/vendas".
"""

from __future__ import annotations

from dataclasses import dataclass

from wealthlab_core.domain.assets import Portfolio
from wealthlab_core.domain.enums import AssetClass
from wealthlab_core.domain.plan import TargetAllocation


@dataclass(frozen=True)
class DeltaClasse:
    classe: AssetClass
    valor_atual: float
    peso_atual: float
    peso_alvo: float
    valor_alvo: float
    delta: float  # alvo − atual (positivo = comprar; negativo = vender)


@dataclass(frozen=True)
class Trade:
    ticker: str
    classe: AssetClass
    acao: str  # "comprar" | "vender" | "manter"
    valor: float  # R$ a movimentar (sempre ≥ 0)


@dataclass(frozen=True)
class RebalanceRecommendation:
    valor_total: float
    por_classe: list[DeltaClasse]
    trades: list[Trade]
    turnover: float  # soma dos |delta| / valor_total (fração movimentada)


def recomendar_rebalanceamento(
    portfolio: Portfolio,
    target: TargetAllocation,
    precos_iniciais: dict[str, float] | None = None,
    tolerancia: float = 0.005,
) -> RebalanceRecommendation:
    """Compara a alocação atual com o alvo e devolve as trades necessárias.

    `tolerancia`: bandas pequenas (|delta| < tolerancia·total) viram "manter".
    Trades por ativo são distribuídas pro-rata ao valor atual dentro da classe.
    """
    precos = precos_iniciais or {}
    holdings = portfolio.holdings
    valores = [h.quantidade * precos.get(h.asset.ticker, 1.0) for h in holdings]
    total = sum(valores)
    if total <= 0:
        raise ValueError("valor total da carteira deve ser positivo.")

    classes = list(dict.fromkeys(h.asset.classe for h in holdings))
    # Classes presentes no alvo, mas ausentes na carteira, também entram.
    for c in target.por_classe:
        if c not in classes:
            classes.append(c)

    valor_classe = {c: 0.0 for c in classes}
    for h, v in zip(holdings, valores):
        valor_classe[h.asset.classe] += v

    # Deltas por classe.
    por_classe: list[DeltaClasse] = []
    for c in classes:
        peso_alvo = target.por_classe.get(c, 0.0)
        valor_alvo = total * peso_alvo
        atual = valor_classe[c]
        por_classe.append(DeltaClasse(
            classe=c, valor_atual=atual, peso_atual=atual / total,
            peso_alvo=peso_alvo, valor_alvo=valor_alvo, delta=valor_alvo - atual,
        ))

    # Trades por ativo: distribui o delta da classe pro-rata ao valor atual.
    delta_por_classe = {d.classe: d.delta for d in por_classe}
    trades: list[Trade] = []
    lim = tolerancia * total
    for h, v in zip(holdings, valores):
        c = h.asset.classe
        base = valor_classe[c]
        share = (v / base) if base > 0 else 0.0
        delta_ativo = delta_por_classe[c] * share
        if abs(delta_ativo) < lim:
            acao = "manter"
        elif delta_ativo > 0:
            acao = "comprar"
        else:
            acao = "vender"
        trades.append(Trade(ticker=h.asset.ticker, classe=c, acao=acao, valor=abs(delta_ativo)))

    turnover = sum(abs(d.delta) for d in por_classe) / 2.0 / total

    return RebalanceRecommendation(
        valor_total=total, por_classe=por_classe, trades=trades, turnover=turnover,
    )
