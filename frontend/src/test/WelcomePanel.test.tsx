import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { WelcomePanel } from '../components/WelcomePanel'
import { CARTEIRA_EXEMPLO } from '../lib/defaultPortfolio'

const base = {
  holdings: CARTEIRA_EXEMPLO,
  onRunExample: () => {},
  onEditPortfolio: () => {},
}

describe('WelcomePanel', () => {
  it('dispara onRunExample ao clicar em Rodar simulação de exemplo', async () => {
    const onRunExample = vi.fn()
    render(<WelcomePanel {...base} onRunExample={onRunExample} />)
    await userEvent.click(screen.getByRole('button', { name: /rodar simula/i }))
    expect(onRunExample).toHaveBeenCalledOnce()
  })

  it('dispara onEditPortfolio ao clicar em Editar minha carteira', async () => {
    const onEditPortfolio = vi.fn()
    render(<WelcomePanel {...base} onEditPortfolio={onEditPortfolio} />)
    await userEvent.click(screen.getByRole('button', { name: /editar minha carteira/i }))
    expect(onEditPortfolio).toHaveBeenCalledOnce()
  })
})
