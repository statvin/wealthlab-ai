import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ErrorState } from '../components/ErrorState'

describe('ErrorState', () => {
  it('dispara onRetry ao clicar em Tentar novamente', async () => {
    const onRetry = vi.fn()
    render(<ErrorState detalhe="boom" onRetry={onRetry} />)
    await userEvent.click(screen.getByRole('button', { name: /tentar novamente/i }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('revela o detalhe técnico só após clicar em Ver detalhes', async () => {
    render(<ErrorState detalhe="ECONNREFUSED 127.0.0.1:8000" onRetry={() => {}} />)
    expect(screen.queryByText(/ECONNREFUSED/)).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /ver detalhes/i }))
    expect(screen.getByText(/ECONNREFUSED/)).toBeInTheDocument()
  })
})
