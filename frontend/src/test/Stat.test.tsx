import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Stat } from '../components/ui/Stat'

describe('Stat', () => {
  it('renderiza label e valor', () => {
    render(<Stat label="Central (P50)" value="R$ 1,2 mi" />)
    expect(screen.getByText('Central (P50)')).toBeInTheDocument()
    expect(screen.getByText('R$ 1,2 mi')).toBeInTheDocument()
  })

  it('expõe gatilho de tooltip acessível quando fornecido', () => {
    render(<Stat label="VaR" value="14%" tooltip="Perda em 1 ano" />)
    expect(screen.getByRole('button', { name: /sobre: var/i })).toBeInTheDocument()
  })
})
