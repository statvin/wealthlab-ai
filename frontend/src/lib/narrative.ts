// Frase-tese: traduz a saída probabilística (P50, faixa, meta, ruína) em uma
// frase de português claro. É o elemento-assinatura do produto. Sem hardcode —
// tudo é derivado dos dados que a API já devolve.

import type { Funil, Resumo } from '../api/types'
import { fmtCompactBRL, fmtPct } from './format'

export type NivelRuina = 'baixo' | 'moderado' | 'alto'

export interface Tese {
  frase: string
  faixaP10: number
  faixaP90: number
  probMeta: number | null
  metaAtingivelAnos: number | null
  nivelRuina: NivelRuina
}

export function nivelDeRuina(probRuina: number): NivelRuina {
  if (probRuina < 0.01) return 'baixo'
  if (probRuina < 0.05) return 'moderado'
  return 'alto'
}

// Primeiro ano em que a mediana (P50) cruza a meta; null se não cruzar no horizonte.
export function metaAtingivelEmAnos(funil: Funil, valorMeta: number): number | null {
  const p50 = funil.bandas['p50']
  if (!p50) return null
  for (let i = 0; i < p50.length; i++) {
    if (p50[i] >= valorMeta) return Math.round(funil.meses[i] / 12)
  }
  return null
}

export function montarTese(
  resumo: Resumo,
  funil: Funil,
  horizonteAnos: number,
  valorMeta: number,
): Tese {
  const nivelRuina = nivelDeRuina(resumo.prob_ruina)
  const anos = `${Math.round(horizonteAnos)} anos`

  const complementos: string[] = []
  if (resumo.prob_meta != null) {
    complementos.push(`${fmtPct(resumo.prob_meta, 0)} de chance de atingir sua meta`)
  }
  complementos.push(`risco de ruína ${nivelRuina}`)

  const frase =
    `Seguindo este plano, você provavelmente chega a ${fmtCompactBRL(resumo.nominal.p50)} ` +
    `em ${anos} — com ${complementos.join(' e ')}.`

  return {
    frase,
    faixaP10: resumo.nominal.p10,
    faixaP90: resumo.nominal.p90,
    probMeta: resumo.prob_meta,
    metaAtingivelAnos: metaAtingivelEmAnos(funil, valorMeta),
    nivelRuina,
  }
}
