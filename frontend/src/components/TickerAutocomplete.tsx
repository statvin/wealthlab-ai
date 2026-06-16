// Autocomplete customizado de tickers (estilo busca): um dropdown abaixo do
// campo que só aparece ao digitar e lista APENAS os ativos cujo ticker ou nome
// COMEÇA com o texto (prefixo). Suporta teclado (↑ ↓ Enter Esc) e clique.

import { useEffect, useRef, useState } from 'react'

import { TICKERS_SUGERIDOS, type TickerSugerido } from '../lib/tickers'

const MAX_SUGESTOES = 8

interface Props {
  value: string
  onChangeText: (texto: string) => void
  onSelect: (t: TickerSugerido) => void
  placeholder?: string
  className?: string
}

export function TickerAutocomplete({ value, onChangeText, onSelect, placeholder, className }: Props) {
  const [aberto, setAberto] = useState(false)
  const [ativo, setAtivo] = useState(0) // índice destacado
  const wrapRef = useRef<HTMLDivElement>(null)

  const q = value.trim().toLowerCase()
  const sugestoes =
    q === ''
      ? []
      : TICKERS_SUGERIDOS.filter(
          (t) =>
            t.ticker.toLowerCase().startsWith(q) || t.nome.toLowerCase().startsWith(q),
        ).slice(0, MAX_SUGESTOES)

  // Fecha ao clicar fora do componente.
  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setAberto(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const escolher = (t: TickerSugerido) => {
    onSelect(t)
    setAberto(false)
  }

  return (
    <div ref={wrapRef} className="relative">
      <input
        value={value}
        placeholder={placeholder}
        autoComplete="off"
        onChange={(e) => {
          onChangeText(e.target.value)
          setAberto(true)
          setAtivo(0)
        }}
        onFocus={() => {
          if (q !== '') setAberto(true)
        }}
        onKeyDown={(e) => {
          if (!aberto || sugestoes.length === 0) return
          if (e.key === 'ArrowDown') {
            e.preventDefault()
            setAtivo((i) => Math.min(i + 1, sugestoes.length - 1))
          } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setAtivo((i) => Math.max(i - 1, 0))
          } else if (e.key === 'Enter') {
            e.preventDefault()
            escolher(sugestoes[ativo])
          } else if (e.key === 'Escape') {
            setAberto(false)
          }
        }}
        className={className}
      />

      {aberto && sugestoes.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-base-600 bg-base-800 shadow-xl">
          {sugestoes.map((t, i) => (
            <li key={t.ticker}>
              <button
                type="button"
                // onMouseDown (com preventDefault) seleciona antes do blur do input.
                onMouseDown={(e) => {
                  e.preventDefault()
                  escolher(t)
                }}
                onMouseEnter={() => setAtivo(i)}
                className={`flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm ${
                  i === ativo ? 'bg-base-600 text-slate-100' : 'text-slate-300'
                }`}
              >
                <span className="font-medium">{t.ticker}</span>
                <span className="truncate text-xs text-slate-400">{t.nome}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
