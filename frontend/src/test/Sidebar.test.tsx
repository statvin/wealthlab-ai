import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Sidebar } from '../components/Sidebar'
import { INPUTS_PADRAO } from '../hooks/useSimulation'

describe('Sidebar', () => {
  it('dispara onRun ao clicar no botão', async () => {
    const onRun = vi.fn()
    render(
      <Sidebar inputs={INPUTS_PADRAO} onChange={() => {}} onRun={onRun} loading={false} />,
    )
    await userEvent.click(screen.getByRole('button', { name: /rodar/i }))
    expect(onRun).toHaveBeenCalledOnce()
  })

  it('desabilita o botão enquanto carrega', () => {
    render(
      <Sidebar inputs={INPUTS_PADRAO} onChange={() => {}} onRun={() => {}} loading={true} />,
    )
    expect(screen.getByRole('button', { name: /rodando/i })).toBeDisabled()
  })
})
