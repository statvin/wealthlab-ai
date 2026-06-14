import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { KpiCard } from '../components/KpiCard'

describe('KpiCard', () => {
  it('renderiza título e valor', () => {
    render(<KpiCard titulo="Mediana (P50)" valor="R$ 1,2 mi" />)
    expect(screen.getByText('Mediana (P50)')).toBeInTheDocument()
    expect(screen.getByText('R$ 1,2 mi')).toBeInTheDocument()
  })

  it('mostra o tooltip quando fornecido', () => {
    render(<KpiCard titulo="VaR" valor="14%" tooltip="Perda em 1 ano" />)
    expect(screen.getByLabelText('Perda em 1 ano')).toBeInTheDocument()
  })
})
