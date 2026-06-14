"""Camada de serviço: converte DTOs ⇄ domínio, chama o motor e monta respostas.

É aqui que a "casca" encosta no núcleo. Nenhuma matemática nova: só orquestração,
serialização (numpy → JSON) e persistência. A validação de domínio é reaproveitada
(construir os objetos do motor já levanta erro em carteira inválida).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
from sqlalchemy.orm import Session

from wealthlab_core.domain import (
    Asset,
    AssetClass,
    CashFlowPlan,
    FinancialGoal,
    FixedIncomeTerms,
    Holding,
    Indexador,
    Portfolio,
    RebalanceMode,
    SimulationConfig,
    TargetAllocation,
)
from wealthlab_core.domain.enums import CLASSES_RENDA_VARIAVEL
from wealthlab_core.engine.estimation import EstimatedParams, estimar_parametros
from wealthlab_core.engine.fixed_income import PremissasJuros
from wealthlab_core.engine.metrics import analisar_risco
from wealthlab_core.engine.simulator import SimulationResult, simular_portfolio
from wealthlab_core.engine.stress import PRESETS, comparar_base_vs_stress
from wealthlab_core.marketdata import MarketDataProvider
from wealthlab_api import models, repository, schemas
from wealthlab_api.config import Settings

# Quantidade de trajetórias-amostra guardadas para o funil (Fase 5).
N_AMOSTRA_FUNIL = 100
PERCENTIS_BANDA = [5, 10, 50, 90, 95]


# --------------------------------------------------------------------------
# Conversões DTO/ORM -> domínio
# --------------------------------------------------------------------------
def _asset_dto_para_dominio(dto: schemas.AssetDTO) -> Asset:
    termos = None
    if dto.fixed_income_terms is not None:
        t = dto.fixed_income_terms
        termos = FixedIncomeTerms(
            indexador=Indexador(t.indexador),
            taxa_contratada=t.taxa_contratada,
            duration_anos=t.duration_anos,
            vencimento=date.fromisoformat(t.vencimento) if t.vencimento else None,
        )
    return Asset(ticker=dto.ticker, nome=dto.nome, classe=AssetClass(dto.classe),
                 fixed_income_terms=termos)


def portfolio_create_para_dominio(
    dto: schemas.PortfolioCreate,
) -> tuple[Portfolio, dict[str, float]]:
    """Constrói o Portfolio de domínio (valida!) e o dicionário de preços."""
    holdings, precos = [], {}
    for h in dto.holdings:
        asset = _asset_dto_para_dominio(h.asset)
        holdings.append(Holding(asset=asset, quantidade=h.quantidade))
        precos[asset.ticker] = h.preco_inicial
    return Portfolio(holdings=holdings), precos


def portfolio_orm_para_dominio(
    orm: models.Portfolio,
) -> tuple[Portfolio, dict[str, float]]:
    holdings, precos = [], {}
    for h in orm.holdings:
        a = h.asset
        termos = None
        if a.fi_indexador is not None:
            termos = FixedIncomeTerms(
                indexador=Indexador(a.fi_indexador),
                taxa_contratada=a.fi_taxa_contratada,
                duration_anos=a.fi_duration_anos or 0.0,
                vencimento=date.fromisoformat(a.fi_vencimento) if a.fi_vencimento else None,
            )
        asset = Asset(ticker=a.ticker, nome=a.nome, classe=AssetClass(a.classe),
                      fixed_income_terms=termos)
        holdings.append(Holding(asset=asset, quantidade=h.quantidade))
        precos[a.ticker] = h.preco_inicial
    return Portfolio(holdings=holdings), precos


def _config_orm_para_dominio(orm: models.SimulationConfig) -> SimulationConfig:
    return SimulationConfig(
        n_cenarios=orm.n_cenarios,
        horizonte_anos=orm.horizonte_anos,
        seed=orm.seed,
        inflacao_aa=orm.inflacao_aa,
        rebalanceamento=RebalanceMode(orm.rebalanceamento),
        df_tstudent=orm.df_tstudent,
    )


def _juros(d: dict) -> PremissasJuros:
    return PremissasJuros(selic_aa=d["selic_aa"], ipca_aa=d["ipca_aa"])


def _cashflow(d: dict | None) -> CashFlowPlan | None:
    if not d:
        return None
    return CashFlowPlan(**d)


def _target(d: dict | None) -> TargetAllocation | None:
    if not d:
        return None
    por_classe = {AssetClass(k): v for k, v in d["por_classe"].items()}
    return TargetAllocation(por_classe=por_classe)


def _goal(d: dict | None) -> FinancialGoal | None:
    if not d:
        return None
    return FinancialGoal(**d)


# --------------------------------------------------------------------------
# Estimação de parâmetros (renda variável) via provider
# --------------------------------------------------------------------------
def estimar_params_rv(
    provider: MarketDataProvider,
    portfolio: Portfolio,
    settings: Settings,
) -> EstimatedParams | None:
    rv = [h.asset.ticker for h in portfolio.holdings if h.asset.classe in CLASSES_RENDA_VARIAVEL]
    if not rv:
        return None
    fim = date.today()
    inicio = fim - timedelta(days=365 * settings.historico_anos)
    precos = provider.get_history(rv, inicio, fim)
    return estimar_parametros(precos)


# --------------------------------------------------------------------------
# Serialização do resultado -> JSON
# --------------------------------------------------------------------------
def _percentis(valores: np.ndarray, qs: list[float]) -> dict[str, float]:
    p = np.percentile(valores, qs)
    return {f"p{int(q)}": float(v) for q, v in zip(qs, p)}


def montar_resultado(
    result: SimulationResult,
    risk,
    goal: FinancialGoal | None,
    params: EstimatedParams | None = None,
) -> dict:
    traj = result.trajetorias_nominais
    traj_real = result.trajetorias_reais()
    finais = traj[:, -1]
    finais_reais = traj_real[:, -1]

    resumo = {
        "patrimonio_inicial": float(traj[0, 0]),
        "nominal": _percentis(finais, [10, 50, 90]),
        "real": _percentis(finais_reais, [10, 50, 90]),
        "prob_ruina": risk.prob_ruina,
        "prob_meta": risk.prob_meta,
    }

    n = min(N_AMOSTRA_FUNIL, traj.shape[0])
    bandas = {f"p{q}": np.percentile(traj, q, axis=0).tolist() for q in PERCENTIS_BANDA}
    funil = {
        "meses": list(range(result.n_passos + 1)),
        "amostra": traj[:n].tolist(),
        "bandas": bandas,
    }

    # Histograma dos patrimônios finais nominais (para o gráfico de distribuição).
    counts, edges = np.histogram(finais, bins=40)
    histograma = {"edges": edges.tolist(), "counts": counts.tolist()}

    # Matriz de correlação da renda variável (para o heatmap). RF não tem
    # correlação no modelo base, então só os ativos de RV aparecem.
    if params is not None:
        correlacao = {"labels": list(params.tickers), "matriz": params.corr.tolist()}
    else:
        correlacao = {"labels": [], "matriz": []}

    risco = {
        "var_cvar": [
            {"nivel": vc.nivel, "var": vc.var, "cvar": vc.cvar}
            for vc in risk.var_cvar.values()
        ],
        "prob_ruina": risk.prob_ruina,
        "prob_meta": risk.prob_meta,
        "drawdown": {
            "medio": risk.drawdown.medio,
            "mediano": risk.drawdown.mediano,
            "pior": risk.drawdown.pior,
        },
        "contribuicao": {
            "ordem": list(risk.contribuicao.ordem),
            "pctr": risk.contribuicao.pctr.tolist(),
            "contrib_vol": risk.contribuicao.contrib_vol.tolist(),
            "vol_anual_carteira": risk.contribuicao.vol_anual_carteira,
            "por_classe": {c.value: v for c, v in risk.contribuicao.por_classe.items()},
        },
    }
    return {
        "resumo": resumo,
        "funil": funil,
        "histograma": histograma,
        "correlacao": correlacao,
        "risco": risco,
    }


# --------------------------------------------------------------------------
# Casos de uso
# --------------------------------------------------------------------------
def criar_carteira(db: Session, dto: schemas.PortfolioCreate) -> models.Portfolio:
    # Valida via domínio antes de persistir (levanta em carteira inválida).
    portfolio_create_para_dominio(dto)
    return repository.create_portfolio(db, dto)


def executar_simulacao(
    db: Session,
    request: schemas.SimulationRunRequest,
    provider: MarketDataProvider,
    settings: Settings,
) -> models.Simulation:
    portfolio_orm = repository.get_portfolio(db, request.portfolio_id)
    if portfolio_orm is None:
        raise LookupError(f"carteira {request.portfolio_id} não encontrada.")

    dominio_pf, precos = portfolio_orm_para_dominio(portfolio_orm)
    params = estimar_params_rv(provider, dominio_pf, settings)

    config = SimulationConfig(
        n_cenarios=request.config.n_cenarios,
        horizonte_anos=request.config.horizonte_anos,
        seed=request.config.seed,
        inflacao_aa=request.config.inflacao_aa,
        rebalanceamento=request.config.rebalanceamento,
        df_tstudent=request.config.df_tstudent,
    )
    juros = _juros(request.premissas_juros.model_dump())
    cashflow = _cashflow(request.cashflow.model_dump() if request.cashflow else None)
    target = _target(request.target.model_dump(mode="json") if request.target else None)
    goal = _goal(request.goal.model_dump() if request.goal else None)

    result = simular_portfolio(
        dominio_pf, config, juros, params_rv=params, cashflow=cashflow,
        target=target, precos_iniciais=precos,
    )
    risk = analisar_risco(
        dominio_pf, config, juros, params_rv=params, cashflow=cashflow,
        target=target, precos_iniciais=precos, goal=goal, result=result,
    )
    resultado = montar_resultado(result, risk, goal, params)

    config_orm = repository.create_config(db, request.config)
    entradas = {
        "premissas_juros": request.premissas_juros.model_dump(),
        "cashflow": request.cashflow.model_dump() if request.cashflow else None,
        "target": request.target.model_dump(mode="json") if request.target else None,
        "goal": request.goal.model_dump() if request.goal else None,
    }
    return repository.create_simulation(
        db, request.portfolio_id, config_orm.id, entradas, resultado, status="concluida"
    )


def rodar_stress(
    db: Session,
    sim: models.Simulation,
    provider: MarketDataProvider,
    settings: Settings,
    presets: list[str] | None = None,
) -> list[dict]:
    """Recomputa Base vs. Stress para os presets pedidos, a partir das entradas
    armazenadas da simulação (reprodutível por seed)."""
    dominio_pf, precos = portfolio_orm_para_dominio(sim.portfolio)
    params = estimar_params_rv(provider, dominio_pf, settings)
    config = _config_orm_para_dominio(sim.config)
    juros = _juros(sim.entradas["premissas_juros"])
    cashflow = _cashflow(sim.entradas.get("cashflow"))
    target = _target(sim.entradas.get("target"))

    nomes = presets or list(PRESETS)
    saida = []
    for nome in nomes:
        cen = PRESETS[nome]
        comp = comparar_base_vs_stress(
            dominio_pf, config, juros, cen, params_rv=params,
            cashflow=cashflow, target=target, precos_iniciais=precos,
        )
        saida.append({
            "nome": nome,
            "descricao": cen.descricao,
            "resumo": {k: [v[0], v[1]] for k, v in comp.resumo.items()},
        })
    return saida
