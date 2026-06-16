// Painel de insights por regras. Cada item mostra a frase e a MÉTRICA que a
// originou (rastreabilidade), com cor por severidade.

import type { Insight } from '../api/types'
import { fmtPct } from '../lib/format'

const COR: Record<string, string> = {
  positivo: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-200',
  neutro: 'border-base-600 bg-base-700/40 text-slate-300',
  atencao: 'border-amber-500/40 bg-amber-500/10 text-amber-200',
  alerta: 'border-rose-500/40 bg-rose-500/10 text-rose-200',
}

const ICONE: Record<string, string> = {
  positivo: '✓',
  neutro: '•',
  atencao: '!',
  alerta: '⚠',
}

export function InsightsPanel({ insights }: { insights: Insight[] }) {
  if (insights.length === 0) return null
  return (
    <div className="card">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">Insights</h3>
      <ul className="space-y-2">
        {insights.map((i, idx) => (
          <li key={idx} className={`rounded-lg border p-3 text-sm ${COR[i.severidade] ?? COR.neutro}`}>
            <span className="mr-2 font-bold">{ICONE[i.severidade] ?? '•'}</span>
            {i.texto}
            <span className="mt-1 block text-xs opacity-70">
              métrica: {i.metrica} = {fmtPct(i.valor)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
