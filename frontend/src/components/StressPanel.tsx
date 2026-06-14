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
        <h3 className="text-sm font-semibold text-slate-300">Stress — Base vs. Cenário</h3>
        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          className="rounded-lg border border-base-600 bg-base-900 px-2 py-1 text-sm"
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
          className="rounded-lg border border-accent px-3 py-1 text-sm text-accent hover:bg-accent hover:text-base-900 disabled:opacity-50"
        >
          {loading ? 'Calculando…' : 'Comparar'}
        </button>
      </div>

      {error && <p className="text-sm text-rose-400">{error}</p>}
      {data && <Tabela comp={data} />}
      {!data && !loading && (
        <p className="text-xs text-slate-500">
          Escolha um cenário e clique em Comparar. Choques estilizados, não replays exatos.
        </p>
      )}
    </div>
  )
}

function Tabela({ comp }: { comp: StressComparacao }) {
  return (
    <>
      <p className="mb-2 text-xs text-slate-400">{comp.descricao}</p>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400">
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
              <tr key={chave} className="border-t border-base-600/50">
                <td className="py-1 text-slate-300">{rotulo}</td>
                <td className="py-1">{fmt(par[0], tipo)}</td>
                <td className="py-1 text-rose-300">{fmt(par[1], tipo)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </>
  )
}
