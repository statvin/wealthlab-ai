"""Renda fixa: evolução não-Browniana, em paralelo ao bloco estocástico.

A renda fixa NÃO usa GBM, NÃO usa Cholesky e NÃO vem do Yahoo. No carrego base
(sem stress) ela é quase-determinística:

  - Pós-fixado (CDI/SELIC): rende um percentual da Selic/CDI projetada. Fator
    mensal constante = (1 + taxa_aa)^(1/12).
  - IPCA+: rende IPCA projetado + juro real contratado. A marcação a mercado via
    duration (ΔP/P ≈ −duration·Δy) só importa sob choque de juros — ou seja, no
    stress (Fase 3). No base, Δy = 0 e o papel apenas carrega.
  - Prefixado: carrego nominal à taxa contratada.

Decisão de projeto: produzimos um FATOR MENSAL por ativo de RF (escalar), que o
orquestrador difunde (broadcast) para todos os cenários. Assim a RF entra no
MESMO array de fatores da renda variável, e a evolução do patrimônio trata todos
os ativos de forma uniforme.

(Hook documentado para o futuro: a spec menciona "opcionalmente pequeno ruído"
no pós-fixado. Fica como extensão — o fator base aqui é determinístico.)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wealthlab_core.domain.assets import Asset
from wealthlab_core.domain.config import PASSOS_POR_ANO
from wealthlab_core.domain.enums import Indexador


@dataclass(frozen=True)
class PremissasJuros:
    """Cenário de juros/inflação projetado para o carrego base da renda fixa.

    `selic_aa`: Selic/CDI projetada (aprox. CDI ≈ Selic no v1).
    `ipca_aa` : IPCA projetado (tipicamente igual à inflação do SimulationConfig).
    """

    selic_aa: float
    ipca_aa: float


def taxa_anual_carrego(asset: Asset, premissas: PremissasJuros) -> float:
    """Taxa nominal anual de carrego do papel, dado o cenário de juros."""
    termos = asset.fixed_income_terms
    if termos is None:  # pragma: no cover - garantido pelo validador do Asset
        raise ValueError(f"{asset.ticker}: ativo de RF sem fixed_income_terms.")

    ind = termos.indexador
    if ind in (Indexador.CDI, Indexador.SELIC):
        # taxa_contratada = percentual do índice (1.0 = 100% do CDI).
        return premissas.selic_aa * termos.taxa_contratada
    if ind == Indexador.IPCA:
        # IPCA+: composição (1+ipca)·(1+juro_real) − 1.
        return (1.0 + premissas.ipca_aa) * (1.0 + termos.taxa_contratada) - 1.0
    if ind == Indexador.PREFIXADO:
        # taxa_contratada = taxa nominal anual.
        return termos.taxa_contratada
    raise ValueError(f"indexador não suportado: {ind}")  # pragma: no cover


def fator_mensal_constante(asset: Asset, premissas: PremissasJuros) -> float:
    """Fator multiplicativo mensal (1 + i_mensal) do papel no carrego base."""
    taxa_aa = taxa_anual_carrego(asset, premissas)
    return (1.0 + taxa_aa) ** (1.0 / PASSOS_POR_ANO)


def gerar_fatores_rf(
    assets_rf: list[Asset],
    premissas: PremissasJuros,
) -> np.ndarray:
    """Vetor (n_rf,) de fatores mensais constantes, na ordem de `assets_rf`.

    O orquestrador difunde este vetor para (n_cenarios, n_passos, n_rf).
    """
    if not assets_rf:
        return np.empty((0,), dtype=float)
    return np.array(
        [fator_mensal_constante(a, premissas) for a in assets_rf], dtype=float
    )
