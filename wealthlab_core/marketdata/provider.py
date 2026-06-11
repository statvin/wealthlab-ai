"""Interface desacoplada de dados de mercado.

O motor nunca fala com o Yahoo diretamente: ele consome um `MarketDataProvider`.
Isso permite trocar a fonte (Yahoo -> Alpha Vantage/Polygon) e, sobretudo,
testar o núcleo com um provedor sintético, sem rede.

Renda fixa NÃO vem deste provider (não é série de preço de mercado): é
parametrizada via `FixedIncomeTerms`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class MarketDataProvider(ABC):
    """Contrato mínimo de uma fonte de histórico de preços.

    Convenção de retorno de `get_history`:
      - DataFrame com índice = datas (DatetimeIndex, ordenado, crescente),
      - uma coluna por ticker (preço de fechamento ajustado),
      - sem NaNs nas datas comuns (o provider concreto deve alinhar/limpar).
    """

    @abstractmethod
    def get_history(
        self,
        tickers: list[str],
        inicio: date,
        fim: date,
    ) -> pd.DataFrame:
        """Retorna o histórico de fechamentos ajustados no intervalo [inicio, fim]."""
        raise NotImplementedError
