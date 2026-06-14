// Utilitários da carteira do usuário.

import type { AssetClass, HoldingDTO, TargetAllocationDTO } from '../api/types'

export const CLASSE_LABEL: Record<AssetClass, string> = {
  EQUITY_BR: 'Ação / ETF Brasil',
  EQUITY_INTL: 'Internacional / ETF',
  CRYPTO: 'Cripto',
  FIXED_INCOME_POS: 'Renda fixa pós (CDI/Selic)',
  FIXED_INCOME_IPCA: 'Renda fixa IPCA+',
}

export const CLASSES: AssetClass[] = [
  'EQUITY_BR',
  'EQUITY_INTL',
  'CRYPTO',
  'FIXED_INCOME_POS',
  'FIXED_INCOME_IPCA',
]

export const ehRendaFixa = (c: AssetClass): boolean =>
  c === 'FIXED_INCOME_POS' || c === 'FIXED_INCOME_IPCA'

export const valorHolding = (h: HoldingDTO): number =>
  h.quantidade * (h.preco_inicial ?? 1)

export const valorTotal = (holdings: HoldingDTO[]): number =>
  holdings.reduce((s, h) => s + valorHolding(h), 0)

// Alvo de rebalanceamento derivado dos PESOS ATUAIS por classe — assim o alvo
// sempre cobre exatamente as classes da carteira (o que o backend exige) e
// rebalancear significa "voltar à alocação inicial".
export function targetFromHoldings(holdings: HoldingDTO[]): TargetAllocationDTO {
  const porClasse: Partial<Record<AssetClass, number>> = {}
  const total = valorTotal(holdings)
  for (const h of holdings) {
    porClasse[h.asset.classe] = (porClasse[h.asset.classe] ?? 0) + valorHolding(h)
  }
  for (const k of Object.keys(porClasse) as AssetClass[]) {
    porClasse[k] = porClasse[k]! / total
  }
  return { por_classe: porClasse }
}

// Pesos por ATIVO (para o resumo da carteira ativa no dashboard).
export function pesosPorAtivo(holdings: HoldingDTO[]): { ticker: string; peso: number }[] {
  const total = valorTotal(holdings)
  return holdings.map((h) => ({ ticker: h.asset.ticker, peso: valorHolding(h) / total }))
}
