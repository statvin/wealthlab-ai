"""Configuração da simulação."""

from __future__ import annotations

from pydantic import BaseModel, Field

from wealthlab_core.domain.enums import RebalanceMode

# Passo fixo mensal (a spec fixa passo=mensal). 12 passos por ano.
PASSOS_POR_ANO = 12


class SimulationConfig(BaseModel):
    """Parâmetros globais de uma simulação Monte Carlo.

    `df_tstudent` controla a gordura da cauda dos choques de renda variável:
      - df baixo (ex.: 4–6)  -> caudas pesadas (crises mais frequentes/intensas).
      - df → ∞               -> recupera o caso normal/lognormal clássico.
    Exigimos df > 2 porque a variância de uma t-Student só é finita nesse caso;
    é também o que permite reescalá-la para casar a volatilidade-alvo (ver
    `engine/returns.py`).

    `seed` garante reprodutibilidade: a mesma config gera exatamente as mesmas
    trajetórias (requisito de engenharia).
    """

    model_config = {"frozen": True}

    n_cenarios: int = Field(default=10_000, gt=0)
    horizonte_anos: float = Field(default=30.0, gt=0)
    seed: int = Field(default=42, ge=0)
    inflacao_aa: float = Field(default=0.04, description="Inflação anual (ex.: 0.04 = 4%).")
    rebalanceamento: RebalanceMode = RebalanceMode.ANUAL_AO_ALVO
    df_tstudent: float = Field(
        default=6.0,
        gt=2.0,
        description="Graus de liberdade da t-Student multivariada (df>2).",
    )

    @property
    def n_passos(self) -> int:
        """Número de passos mensais no horizonte (arredonda para o mês cheio)."""
        return int(round(self.horizonte_anos * PASSOS_POR_ANO))
