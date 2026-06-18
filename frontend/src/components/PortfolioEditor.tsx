// Editor da carteira do usuário: adiciona/remove ativos por classe. A carteira
// montada aqui é o que o sistema simula (vira POST /portfolio).

import { useState } from 'react'

import type { AssetClass, HoldingDTO, Indexador } from '../api/types'
import { fmtBRL, fmtPct } from '../lib/format'
import { CLASSE_LABEL, CLASSES, ehRendaFixa, valorHolding, valorTotal } from '../lib/portfolio'
import { buscarTicker } from '../lib/tickers'
import { NumberField } from './NumberField'
import { TickerAutocomplete } from './TickerAutocomplete'

const INDEXADORES: Indexador[] = ['CDI', 'SELIC', 'IPCA', 'PREFIXADO']

const NOVO_VAZIO = {
  ticker: '',
  nome: '',
  classe: 'EQUITY_BR' as AssetClass,
  quantidade: 0,
  preco_inicial: 0,
  indexador: 'CDI' as Indexador,
  taxa_contratada: 1.0,
  duration_anos: 0,
}

const inputCls =
  'w-full rounded-lg border border-border bg-canvas px-3 py-2 text-sm text-content focus:border-brand focus:outline-none'

export function PortfolioEditor({
  holdings,
  onChange,
}: {
  holdings: HoldingDTO[]
  onChange: (h: HoldingDTO[]) => void
}) {
  const [novo, setNovo] = useState(NOVO_VAZIO)
  const [erro, setErro] = useState<string | null>(null)
  const total = valorTotal(holdings)
  const rf = ehRendaFixa(novo.classe)

  function adicionar() {
    const ticker = novo.ticker.trim()
    if (!ticker) return setErro('Informe o ticker (ex.: WEGE3.SA, BTC-USD).')
    if (novo.quantidade <= 0) return setErro('Quantidade deve ser maior que zero.')
    if (novo.preco_inicial <= 0) return setErro('Preço inicial deve ser maior que zero.')
    if (holdings.some((h) => h.asset.ticker === ticker))
      return setErro('Esse ticker já está na carteira.')

    const holding: HoldingDTO = {
      asset: {
        ticker,
        nome: novo.nome.trim() || ticker,
        classe: novo.classe,
        fixed_income_terms: rf
          ? {
              indexador: novo.indexador,
              taxa_contratada: novo.taxa_contratada,
              duration_anos: novo.duration_anos,
            }
          : null,
      },
      quantidade: novo.quantidade,
      preco_inicial: novo.preco_inicial,
    }
    onChange([...holdings, holding])
    setNovo(NOVO_VAZIO)
    setErro(null)
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <h3 className="mb-3 text-sm font-semibold text-content-body">Minha carteira</h3>
        {holdings.length === 0 ? (
          <p className="text-sm text-content-subtle">
            Carteira vazia. Adicione ativos abaixo para simular sobre eles.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-content-muted">
                <th className="font-medium">Classe</th>
                <th className="font-medium">Ativo</th>
                <th className="font-medium text-right">Qtd</th>
                <th className="font-medium text-right">Preço</th>
                <th className="font-medium text-right">Valor</th>
                <th className="font-medium text-right">Peso</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <tr key={h.asset.ticker} className="border-t border-border">
                  <td className="py-1 text-content-muted">{CLASSE_LABEL[h.asset.classe]}</td>
                  <td className="py-1">
                    <span className="font-medium text-content">{h.asset.ticker}</span>
                    {h.asset.fixed_income_terms && (
                      <span className="ml-1 text-xs text-content-subtle">
                        {h.asset.fixed_income_terms.indexador} {h.asset.fixed_income_terms.taxa_contratada}
                      </span>
                    )}
                  </td>
                  <td className="py-1 text-right">{h.quantidade}</td>
                  <td className="py-1 text-right">{fmtBRL(h.preco_inicial ?? 1)}</td>
                  <td className="py-1 text-right">{fmtBRL(valorHolding(h))}</td>
                  <td className="py-1 text-right text-content-muted">
                    {total > 0 ? fmtPct(valorHolding(h) / total) : '—'}
                  </td>
                  <td className="py-1 text-right">
                    <button
                      onClick={() => onChange(holdings.filter((x) => x.asset.ticker !== h.asset.ticker))}
                      className="text-loss transition-colors hover:text-loss/70"
                      aria-label={`Remover ${h.asset.ticker}`}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
              <tr className="border-t border-border">
                <td colSpan={4} className="py-1 font-medium text-content-body">
                  Total
                </td>
                <td className="py-1 text-right font-medium text-content">{fmtBRL(total)}</td>
                <td colSpan={2} />
              </tr>
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold text-content-body">Adicionar ativo</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label className="block">
            <span className="label">Classe</span>
            <select
              value={novo.classe}
              onChange={(e) => setNovo({ ...novo, classe: e.target.value as AssetClass })}
              className={`mt-1 ${inputCls}`}
            >
              {CLASSES.map((c) => (
                <option key={c} value={c}>
                  {CLASSE_LABEL[c]}
                </option>
              ))}
            </select>
          </label>

          <div className="block">
            <span className="label">Ticker</span>
            <TickerAutocomplete
              value={novo.ticker}
              placeholder={rf ? 'ex.: TD-IPCA-2035' : 'ex.: PETR4.SA'}
              onChangeText={(ticker) => {
                const m = buscarTicker(ticker)
                // Se o texto digitado já casar um ticker conhecido, preenche nome/classe.
                setNovo((n) => ({ ...n, ticker, ...(m ? { nome: m.nome, classe: m.classe } : {}) }))
              }}
              onSelect={(t) =>
                setNovo((n) => ({ ...n, ticker: t.ticker, nome: t.nome, classe: t.classe }))
              }
              className={`mt-1 ${inputCls}`}
            />
          </div>

          <label className="block">
            <span className="label">Nome (opcional)</span>
            <input
              value={novo.nome}
              onChange={(e) => setNovo({ ...novo, nome: e.target.value })}
              className={`mt-1 ${inputCls}`}
            />
          </label>

          <label className="block">
            <span className="label">Quantidade</span>
            <NumberField
              value={novo.quantidade}
              onChange={(v) => setNovo({ ...novo, quantidade: v })}
              className={`mt-1 ${inputCls}`}
            />
          </label>

          <label className="block">
            <span className="label">Preço inicial (R$)</span>
            <NumberField
              value={novo.preco_inicial}
              onChange={(v) => setNovo({ ...novo, preco_inicial: v })}
              className={`mt-1 ${inputCls}`}
            />
          </label>

          {rf && (
            <>
              <label className="block">
                <span className="label">Indexador</span>
                <select
                  value={novo.indexador}
                  onChange={(e) => setNovo({ ...novo, indexador: e.target.value as Indexador })}
                  className={`mt-1 ${inputCls}`}
                >
                  {INDEXADORES.map((i) => (
                    <option key={i} value={i}>
                      {i}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="label">
                  Taxa{' '}
                  <span className="normal-case text-content-subtle">
                    (CDI: % do índice; IPCA/pré: a.a.)
                  </span>
                </span>
                <NumberField
                  value={novo.taxa_contratada}
                  onChange={(v) => setNovo({ ...novo, taxa_contratada: v })}
                  step="0.01"
                  className={`mt-1 ${inputCls}`}
                />
              </label>
              <label className="block">
                <span className="label">Duration (anos)</span>
                <NumberField
                  value={novo.duration_anos}
                  onChange={(v) => setNovo({ ...novo, duration_anos: v })}
                  step="0.5"
                  className={`mt-1 ${inputCls}`}
                />
              </label>
            </>
          )}
        </div>

        {erro && <p className="mt-2 text-sm text-loss">{erro}</p>}

        <button
          onClick={adicionar}
          className="mt-3 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong"
        >
          Adicionar à carteira
        </button>
      </div>
    </div>
  )
}
