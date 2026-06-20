import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { SimulationInputs } from '../components/SimulationInputs'
import { INPUTS_PADRAO } from '../hooks/useSimulation'
import { CARTEIRA_EXEMPLO } from '../lib/defaultPortfolio'

const base = {
  holdings: CARTEIRA_EXEMPLO,
  inputs: INPUTS_PADRAO,
  onChange: () => {},
  onEditCarteira: () => {},
}

describe('SimulationInputs', () => {
  it('dispara onRun ao clicar em Rodar simulação', async () => {
    const onRun = vi.fn()
    render(<SimulationInputs {...base} onRun={onRun} loading={false} />)
    await userEvent.click(screen.getByRole('button', { name: /rodar simula/i }))
    expect(onRun).toHaveBeenCalledOnce()
  })

  it('desabilita o botão enquanto carrega', () => {
    render(<SimulationInputs {...base} onRun={() => {}} loading={true} />)
    expect(screen.getByRole('button', { name: /rodando/i })).toBeDisabled()
  })
})
