// Formatação localizada (pt-BR): moeda, percentual e números compactos.

const brl = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

const compact = new Intl.NumberFormat('pt-BR', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export const fmtBRL = (v: number): string => brl.format(v)

export const fmtCompactBRL = (v: number): string => `R$ ${compact.format(v)}`

export const fmtPct = (v: number, casas = 1): string => `${(v * 100).toFixed(casas)}%`
