// Painel de insights por regras. Cada item mostra a frase e a MÉTRICA que a
// originou (rastreabilidade), com cor por severidade.

import type { Insight } from '../api/types'
import { fmtPct } from '../lib/format'

const COR: Record<string, string> = {
  positivo: 'border-gain/40 bg-gain/10 text-gain',
  neutro: 'border-border bg-canvas text-content-body',
  atencao: 'border-warning/40 bg-warning/10 text-warning',
  alerta: 'border-loss/40 bg-loss/10 text-loss',
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
      <h3 className="mb-3 text-sm font-semibold text-content-body">Insights</h3>
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
