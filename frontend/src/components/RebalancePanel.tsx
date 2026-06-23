// Recomendação de rebalanceamento: o usuário define a alocação-alvo por classe
// e recebe as compras/vendas. Distinto do rebalanceamento DENTRO da simulação.

import { useState } from 'react'

import type { AssetClass, HoldingDTO } from '../api/types'
import { useRebalance } from '../hooks/useRebalance'
import { fmtBRL, fmtPct } from '../lib/format'
import { CLASSE_LABEL, targetFromHoldings } from '../lib/portfolio'
import { NumberField } from './NumberField'

const inputCls =
  'w-full rounded-lg border border-border bg-canvas px-3 py-2 text-sm text-content focus:border-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/50'

const CORACAO: Record<string, string> = {
  comprar: 'text-gain',
  vender: 'text-loss',
  manter: 'text-content-subtle',
}

export function RebalancePanel({ simId, holdings }: { simId: number; holdings: HoldingDTO[] }) {
  const classes = [...new Set(holdings.map((h) => h.asset.classe))]
  const atual = targetFromHoldings(holdings).por_classe

  // Alvo inicial = alocação atual (em %), para o usuário ajustar.
  const [alvo, setAlvo] = useState<Record<string, number>>(() =>
    Object.fromEntries(classes.map((c) => [c, Math.round((atual[c] ?? 0) * 1000) / 10])),
  )
  const { loading, error, data, run } = useRebalance(simId)
  const soma = Object.values(alvo).reduce((s, v) => s + v, 0)
  const somaOk = Math.abs(soma - 100) < 0.1

  const calcular = () => {
    const por_classe = Object.fromEntries(
      Object.entries(alvo).map(([c, v]) => [c, v / 100]),
    ) as Record<AssetClass, number>
    run({ por_classe })
  }

  return (
    <div className="card">
      <h3 className="mb-1 text-sm font-semibold text-content-body">Rebalanceamento da carteira</h3>
      <p className="mb-3 text-xs text-content-subtle">
        Defina a alocação-alvo por classe. É uma recomendação pontual de compras/vendas — distinta
        do rebalanceamento que ocorre dentro da simulação.
      </p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {classes.map((c) => (
          <label key={c} className="block">
            <span className="label">{CLASSE_LABEL[c]} (%)</span>
            <NumberField
              value={alvo[c]}
              step="1"
              onChange={(v) => setAlvo({ ...alvo, [c]: v })}
              className={`mt-1 ${inputCls}`}
            />
          </label>
        ))}
      </div>

      <div className="mt-2 flex items-center gap-3">
        <span className={`text-xs ${somaOk ? 'text-content-muted' : 'text-warning'}`}>
          Soma: {soma.toFixed(1)}% {somaOk ? '' : '(deve ser 100%)'}
        </span>
        <button
          onClick={calcular}
          disabled={loading || !somaOk}
          className="rounded-lg border border-brand px-3 py-1 text-sm text-brand transition-colors hover:bg-brand hover:text-on-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50"
        >
          {loading ? 'Calculando…' : 'Calcular'}
        </button>
      </div>

      {error && <p className="mt-2 text-sm text-loss">{error}</p>}

      {data && (
        <div className="mt-4">
          <p className="mb-2 text-xs text-content-muted">
            Movimentação total (turnover): {fmtPct(data.turnover)} do patrimônio.
          </p>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-content-muted">
                <th className="font-medium">Ativo</th>
                <th className="font-medium">Ação</th>
                <th className="font-medium text-right">Valor</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.map((t) => (
                <tr key={t.ticker} className="border-t border-border">
                  <td className="py-1">{t.ticker}</td>
                  <td className={`py-1 ${CORACAO[t.acao] ?? ''}`}>{t.acao}</td>
                  <td className="py-1 text-right">{t.acao === 'manter' ? '—' : fmtBRL(t.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
