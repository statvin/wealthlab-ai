"""Insights baseados em REGRAS (sem API externa).

Cada insight é gerado a partir de uma métrica e carrega o nome e o valor dessa
métrica — ou seja, toda afirmação é RASTREÁVEL ao número que a originou (critério
de aceite da Fase 6). Os limiares são explícitos e ajustáveis aqui.
"""

from __future__ import annotations

from dataclasses import dataclass

from wealthlab_core.domain.assets import Portfolio
from wealthlab_core.domain.enums import AssetClass
from wealthlab_core.domain.plan import CashFlowPlan
from wealthlab_core.engine.metrics import RiskAnalysis, pesos_iniciais

# Limiares (ajustáveis) das regras.
META_ALTA = 0.80
META_MEDIA = 0.50
CONCENTRACAO_CLASSE = 0.50
CRIPTO_ALERTA = 0.15
RISCO_CONCENTRADO = 0.50
RUINA_ALERTA = 0.10
TAXA_RETIRADA_SEGURA = 0.04  # ~regra dos 4% a.a.
DRAWDOWN_SEVERO = 0.50

Severidade = str  # "positivo" | "neutro" | "atencao" | "alerta"


@dataclass(frozen=True)
class Insight:
    categoria: str
    severidade: Severidade
    texto: str
    metrica: str
    valor: float


def _pesos_por_classe(portfolio: Portfolio, precos: dict[str, float] | None) -> dict[AssetClass, float]:
    pesos, _ = pesos_iniciais(portfolio, precos)
    por_classe: dict[AssetClass, float] = {}
    for h, w in zip(portfolio.holdings, pesos):
        por_classe[h.asset.classe] = por_classe.get(h.asset.classe, 0.0) + float(w)
    return por_classe


def gerar_insights(
    portfolio: Portfolio,
    risk: RiskAnalysis,
    precos_iniciais: dict[str, float] | None = None,
    cashflow: CashFlowPlan | None = None,
    valor_inicial: float | None = None,
) -> list[Insight]:
    """Gera a lista de insights a partir da carteira e da análise de risco."""
    insights: list[Insight] = []
    pct = lambda x: f"{x * 100:.1f}%"  # noqa: E731 - formatação local

    # 1) Probabilidade de meta.
    if risk.prob_meta is not None:
        pm = risk.prob_meta
        if pm >= META_ALTA:
            insights.append(Insight("meta", "positivo",
                f"Alta probabilidade de atingir a meta ({pct(pm)}). O plano está no rumo.",
                "prob_meta", pm))
        elif pm >= META_MEDIA:
            insights.append(Insight("meta", "neutro",
                f"Probabilidade moderada de meta ({pct(pm)}). Pequenos ajustes de aporte ou prazo ajudam.",
                "prob_meta", pm))
        else:
            insights.append(Insight("meta", "atencao",
                f"Probabilidade baixa de meta ({pct(pm)}). Considere aumentar aporte, alongar o prazo "
                f"ou rever a exposição a risco.",
                "prob_meta", pm))

    # 2) Concentração por classe.
    por_classe = _pesos_por_classe(portfolio, precos_iniciais)
    if por_classe:
        classe_top, peso_top = max(por_classe.items(), key=lambda x: x[1])
        if peso_top > CONCENTRACAO_CLASSE:
            insights.append(Insight("concentracao", "atencao",
                f"Carteira concentrada em {classe_top.value} ({pct(peso_top)}). "
                f"Diversificar entre classes reduz risco específico.",
                f"peso_classe:{classe_top.value}", peso_top))

    # 3) Peso de cripto (com o aviso de cauda subestimada do modelo).
    peso_cripto = por_classe.get(AssetClass.CRYPTO, 0.0)
    if peso_cripto > CRIPTO_ALERTA:
        insights.append(Insight("cripto", "alerta",
            f"Cripto representa {pct(peso_cripto)} da carteira. O risco de cauda é elevado e, "
            f"no modelo atual, tende a ser SUBESTIMADO — trate como cenário otimista de risco.",
            "peso_cripto", peso_cripto))

    # 4) Contribuição ao risco concentrada em um ativo.
    ranking = risk.contribuicao.ranking()
    if ranking:
        ticker_top, pctr_top = ranking[0]
        if pctr_top > RISCO_CONCENTRADO:
            insights.append(Insight("risco", "atencao",
                f"{ticker_top} concentra {pct(pctr_top)} do risco da carteira, "
                f"apesar de ser uma fração menor do patrimônio.",
                f"pctr:{ticker_top}", pctr_top))

    # 5) Sustentabilidade do saque.
    if risk.prob_ruina > RUINA_ALERTA:
        insights.append(Insight("saque", "alerta",
            f"Risco de ruína de {pct(risk.prob_ruina)} antes do fim do horizonte — "
            f"o saque pode ser insustentável. Reduza a retirada ou aumente o patrimônio.",
            "prob_ruina", risk.prob_ruina))

    if cashflow is not None and cashflow.saque_mensal > 0 and valor_inicial and valor_inicial > 0:
        taxa = cashflow.saque_mensal * 12 / valor_inicial
        if taxa > TAXA_RETIRADA_SEGURA:
            insights.append(Insight("saque", "atencao",
                f"Taxa de retirada de {pct(taxa)} a.a., acima da faixa usualmente considerada "
                f"segura (~{pct(TAXA_RETIRADA_SEGURA)}).",
                "taxa_retirada", taxa))

    # 6) Drawdown severo.
    dd = risk.drawdown.pior
    if dd > DRAWDOWN_SEVERO:
        insights.append(Insight("drawdown", "neutro",
            f"No pior caso simulado, o patrimônio chega a cair {pct(dd)} do pico. "
            f"Quedas grandes fazem parte — evite resgatar no fundo.",
            "drawdown_pior", dd))

    return insights
