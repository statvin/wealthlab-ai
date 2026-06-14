import { describe, expect, it } from 'vitest'

import { fmtBRL, fmtPct } from '../lib/format'

describe('format', () => {
  it('formata percentual com 1 casa por padrão', () => {
    expect(fmtPct(0.1234)).toBe('12.3%')
  })

  it('respeita o número de casas', () => {
    expect(fmtPct(0.5, 0)).toBe('50%')
  })

  it('formata moeda em BRL', () => {
    // separador de milhar pt-BR é ponto; o símbolo pode vir com espaço especial.
    expect(fmtBRL(1000)).toContain('1.000')
  })
})
