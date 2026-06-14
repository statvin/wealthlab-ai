// Painel de risco: VaR/CVaR (1 ano), drawdown e contribuição ao risco (barras).

import type { RiskAnalysisOut } from '../api/types'
import { fmtPct } from '../lib/format'

export function RiskPanel({ risk }: { risk: RiskAnalysisOut }) {
  const vc = (nivel: number) => risk.var_cvar.find((v) => v.nivel === nivel)

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="card">
        <h3 className="mb-3 text-sm font-semibold text-slate-300">
          Risco de mercado — retorno em 1 ano
        </h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-400">
              <th className="font-medium">Nível</th>
              <th className="font-medium">VaR</th>
              <th className="font-medium">CVaR</th>
            </tr>
          </thead>
          <tbody>
            {[0.95, 0.99].map((n) => (
              <tr key={n} className="border-t border-base-600/50">
                <td className="py-1">{fmtPct(n, 0)}</td>
                <td className="py-1 text-rose-300">{fmtPct(vc(n)?.var ?? 0)}</td>
                <td className="py-1 text-rose-400">{fmtPct(vc(n)?.cvar ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-xs text-slate-400">
          Drawdown — médio {fmtPct(risk.drawdown.medio)} · mediano{' '}
          {fmtPct(risk.drawdown.mediano)} · pior {fmtPct(risk.drawdown.pior)}
        </p>
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold text-slate-300">
          Contribuição ao risco{' '}
          <span className="font-normal text-slate-500">
            (vol. anual {fmtPct(risk.contribuicao.vol_anual_carteira)})
          </span>
        </h3>
        <div className="space-y-2">
          {risk.contribuicao.ordem.map((ticker, i) => {
            const pct = risk.contribuicao.pctr[i]
            return (
              <div key={ticker}>
                <div className="flex justify-between text-xs text-slate-300">
                  <span>{ticker}</span>
                  <span>{fmtPct(pct)}</span>
                </div>
                <div className="mt-0.5 h-2 rounded bg-base-600/50">
                  <div
                    className="h-2 rounded bg-accent"
                    style={{ width: `${Math.max(pct * 100, 0).toFixed(1)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
