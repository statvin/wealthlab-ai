"""Enumerações do domínio.

Usamos `str, Enum` para que os valores serializem como strings legíveis em JSON
(útil quando a API da Fase 4 expor estes tipos) e sejam comparáveis a strings.
"""

from __future__ import annotations

from enum import Enum


class AssetClass(str, Enum):
    """Classes de ativo suportadas.

    A separação POS x IPCA dentro de renda fixa não é cosmética: cada uma tem um
    modelo de evolução próprio (ver `engine/fixed_income.py`).
      - POS  (pós-fixado, Selic/CDI): carrego quase-determinístico.
      - IPCA (IPCA+): carrego real + risco de marcação a mercado via duration.
    """

    EQUITY_BR = "EQUITY_BR"          # ações/ETFs Brasil (B3, sufixo .SA)
    EQUITY_INTL = "EQUITY_INTL"      # ações/ETFs internacionais (ou BDR/ETF cambial)
    CRYPTO = "CRYPTO"                # cripto (t-Student de cauda pesada)
    FIXED_INCOME_POS = "FIXED_INCOME_POS"    # renda fixa pós-fixada (Selic/CDI)
    FIXED_INCOME_IPCA = "FIXED_INCOME_IPCA"  # renda fixa IPCA+ (com duration)


# Conjuntos auxiliares para validação/roteamento no motor.
CLASSES_RENDA_VARIAVEL = frozenset(
    {AssetClass.EQUITY_BR, AssetClass.EQUITY_INTL, AssetClass.CRYPTO}
)
CLASSES_RENDA_FIXA = frozenset(
    {AssetClass.FIXED_INCOME_POS, AssetClass.FIXED_INCOME_IPCA}
)


class Indexador(str, Enum):
    """Indexador de um papel de renda fixa.

    Define a interpretação de `FixedIncomeTerms.taxa_contratada`:
      - CDI/SELIC : taxa_contratada = percentual do índice (ex.: 1.0 = 100% do CDI).
      - IPCA      : taxa_contratada = juro real anual (ex.: 0.06 = IPCA + 6% a.a.).
      - PREFIXADO : taxa_contratada = taxa nominal anual (ex.: 0.11 = 11% a.a.).
    """

    CDI = "CDI"
    SELIC = "SELIC"
    IPCA = "IPCA"
    PREFIXADO = "PREFIXADO"


class RebalanceMode(str, Enum):
    """Modo de rebalanceamento *dentro* da simulação.

    Distinto do rebalanceamento-recomendação da Fase 6 (que olha a carteira real
    e sugere compras/vendas). Aqui é o que acontece ao longo das trajetórias.
    """

    NENHUM = "NENHUM"                # buy-and-hold
    ANUAL_AO_ALVO = "ANUAL_AO_ALVO"  # a cada 12 passos, realoca aos pesos-alvo
