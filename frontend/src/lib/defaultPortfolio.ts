// Carteira-EXEMPLO usada apenas como estado INICIAL do editor (o usuário pode
// editar/remover/limpar e inserir os próprios ativos). Não é mais fixa.
// Os tickers de RV precisam de dados de mercado (Yahoo cache-first); para a demo
// offline, ver scripts/seed_cache.py.

import type { PortfolioCreate } from '../api/types'

export const CARTEIRA_EXEMPLO: PortfolioCreate['holdings'] = [
  {
    asset: { ticker: 'PETR4.SA', nome: 'Petrobras PN', classe: 'EQUITY_BR' },
    quantidade: 500,
    preco_inicial: 38,
  },
  {
    asset: { ticker: 'IVVB11.SA', nome: 'S&P 500 (BRL)', classe: 'EQUITY_INTL' },
    quantidade: 100,
    preco_inicial: 340,
  },
  {
    asset: { ticker: 'BTC-USD', nome: 'Bitcoin', classe: 'CRYPTO' },
    quantidade: 0.05,
    preco_inicial: 350000,
  },
  {
    asset: {
      ticker: 'CDB-CDI',
      nome: 'CDB 100% CDI',
      classe: 'FIXED_INCOME_POS',
      fixed_income_terms: { indexador: 'CDI', taxa_contratada: 1.0 },
    },
    quantidade: 30000,
    preco_inicial: 1,
  },
]
