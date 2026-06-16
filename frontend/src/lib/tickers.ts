// Lista curada de ativos para o autocomplete (datalist) ao adicionar à carteira.
// Não é exaustiva — é uma conveniência. Qualquer ticker válido pode ser digitado
// à mão; os dados de mercado vêm do Yahoo (cache-first). Ao escolher um item
// daqui, nome e classe são preenchidos automaticamente.

import type { AssetClass } from '../api/types'

export interface TickerSugerido {
  ticker: string
  nome: string
  classe: AssetClass
}

export const TICKERS_SUGERIDOS: TickerSugerido[] = [
  // Ações Brasil (B3, sufixo .SA)
  { ticker: 'PETR4.SA', nome: 'Petrobras PN', classe: 'EQUITY_BR' },
  { ticker: 'PETR3.SA', nome: 'Petrobras ON', classe: 'EQUITY_BR' },
  { ticker: 'VALE3.SA', nome: 'Vale ON', classe: 'EQUITY_BR' },
  { ticker: 'ITUB4.SA', nome: 'Itaú Unibanco PN', classe: 'EQUITY_BR' },
  { ticker: 'BBDC4.SA', nome: 'Bradesco PN', classe: 'EQUITY_BR' },
  { ticker: 'BBAS3.SA', nome: 'Banco do Brasil ON', classe: 'EQUITY_BR' },
  { ticker: 'ABEV3.SA', nome: 'Ambev ON', classe: 'EQUITY_BR' },
  { ticker: 'WEGE3.SA', nome: 'WEG ON', classe: 'EQUITY_BR' },
  { ticker: 'ITSA4.SA', nome: 'Itaúsa PN', classe: 'EQUITY_BR' },
  { ticker: 'B3SA3.SA', nome: 'B3 ON', classe: 'EQUITY_BR' },
  { ticker: 'MGLU3.SA', nome: 'Magazine Luiza ON', classe: 'EQUITY_BR' },
  { ticker: 'RENT3.SA', nome: 'Localiza ON', classe: 'EQUITY_BR' },
  { ticker: 'PRIO3.SA', nome: 'PRIO ON', classe: 'EQUITY_BR' },
  { ticker: 'SUZB3.SA', nome: 'Suzano ON', classe: 'EQUITY_BR' },
  { ticker: 'RADL3.SA', nome: 'Raia Drogasil ON', classe: 'EQUITY_BR' },
  { ticker: 'ELET3.SA', nome: 'Eletrobras ON', classe: 'EQUITY_BR' },

  // ETFs negociados na B3
  { ticker: 'BOVA11.SA', nome: 'iShares Ibovespa', classe: 'EQUITY_BR' },
  { ticker: 'SMAL11.SA', nome: 'iShares Small Caps', classe: 'EQUITY_BR' },
  { ticker: 'IVVB11.SA', nome: 'iShares S&P 500 (BRL)', classe: 'EQUITY_INTL' },
  { ticker: 'NASD11.SA', nome: 'ETF Nasdaq-100 (BRL)', classe: 'EQUITY_INTL' },
  { ticker: 'HASH11.SA', nome: 'Hashdex Cripto', classe: 'CRYPTO' },

  // Cripto (par com USD no Yahoo)
  { ticker: 'BTC-USD', nome: 'Bitcoin', classe: 'CRYPTO' },
  { ticker: 'ETH-USD', nome: 'Ethereum', classe: 'CRYPTO' },
  { ticker: 'SOL-USD', nome: 'Solana', classe: 'CRYPTO' },
]

export function buscarTicker(ticker: string): TickerSugerido | undefined {
  const t = ticker.trim().toLowerCase()
  return TICKERS_SUGERIDOS.find((x) => x.ticker.toLowerCase() === t)
}
