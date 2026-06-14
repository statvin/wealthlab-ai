import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PortfolioEditor } from '../components/PortfolioEditor'

describe('PortfolioEditor', () => {
  it('adiciona um ativo informado pelo usuário', async () => {
    const onChange = vi.fn()
    render(<PortfolioEditor holdings={[]} onChange={onChange} />)

    await userEvent.type(screen.getByPlaceholderText(/WEGE3/i), 'WEGE3.SA')
    const nums = screen.getAllByRole('spinbutton') // [quantidade, preço]
    await userEvent.clear(nums[0])
    await userEvent.type(nums[0], '10')
    await userEvent.clear(nums[1])
    await userEvent.type(nums[1], '50')
    await userEvent.click(screen.getByRole('button', { name: /adicionar/i }))

    expect(onChange).toHaveBeenCalledTimes(1)
    const novaCarteira = onChange.mock.calls[0][0]
    expect(novaCarteira[0].asset.ticker).toBe('WEGE3.SA')
    expect(novaCarteira[0].quantidade).toBe(10)
  })

  it('rejeita ticker vazio', async () => {
    const onChange = vi.fn()
    render(<PortfolioEditor holdings={[]} onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: /adicionar/i }))
    expect(onChange).not.toHaveBeenCalled()
    expect(screen.getByText(/informe o ticker/i)).toBeInTheDocument()
  })
})
