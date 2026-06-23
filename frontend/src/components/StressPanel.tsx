// Comparação Base vs. Stress: escolhe um preset e busca a comparação sob demanda.

import { useState } from 'react'

import type { StressComparacao } from '../api/types'
import { useStress } from '../hooks/useStress'
import { fmtCompactBRL, fmtPct } from '../lib/format'

const PRESETS = ['2008', 'COVID-2020', 'Estagflacao', 'Brasil-2015']

const LINHAS: { chave: string; rotulo: string; fmt: 'money' | 'pct' }[] = [
  { chave: 'p50_final', rotulo: 'Patrimônio P50', fmt: 'money' },
  { chave: 'p10_final', rotulo: 'Patrimônio P10', fmt: 'money' },
  { chave: 'var_95_1ano', rotulo: 'VaR 95% (1 ano)', fmt: 'pct' },
  { chave: 'cvar_95_1ano', rotulo: 'CVaR 95% (1 ano)', fmt: 'pct' },
  { chave: 'drawdown_pior', rotulo: 'Drawdown pior', fmt: 'pct' },
  { chave: 'prob_ruina', rotulo: 'Prob. de ruína', fmt: 'pct' },
]

function fmt(v: number, tipo: 'money' | 'pct') {
  return tipo === 'money' ? fmtCompactBRL(v) : fmtPct(v)
}

export function StressPanel({ simId }: { simId: number }) {
  const [preset, setPreset] = useState(PRESETS[0])
  const { loading, error, data, run } = useStress(simId)

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-content-body">Stress — Base vs. Cenário</h3>
        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          className="rounded-lg border border-border bg-canvas px-2 py-1 text-sm text-content focus:border-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/50"
        >
          {PRESETS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <button
          onClick={() => run(preset)}
          disabled={loading}
          className="rounded-lg border border-brand px-3 py-1 text-sm text-brand transition-colors hover:bg-brand hover:text-on-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50"
        >
          {loading ? 'Calculando…' : 'Comparar'}
        </button>
      </div>

      {error && <p className="text-sm text-loss">{error}</p>}
      {data && <Tabela comp={data} />}
      {!data && !loading && (
        <p className="text-xs text-content-subtle">
          Escolha um cenário e clique em Comparar. Choques estilizados, não replays exatos.
        </p>
      )}
    </div>
  )
}

function Tabela({ comp }: { comp: StressComparacao }) {
  return (
    <>
      <p className="mb-2 text-xs text-content-muted">{comp.descricao}</p>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-content-muted">
            <th className="font-medium">Métrica</th>
            <th className="font-medium">Base</th>
            <th className="font-medium">Stress</th>
          </tr>
        </thead>
        <tbody>
          {LINHAS.map(({ chave, rotulo, fmt: tipo }) => {
            const par = comp.resumo[chave]
            if (!par) return null
            return (
              <tr key={chave} className="border-t border-border">
                <td className="py-1 text-content-body">{rotulo}</td>
                <td className="py-1">{fmt(par[0], tipo)}</td>
                <td className="py-1 text-loss">{fmt(par[1], tipo)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </>
  )
}
