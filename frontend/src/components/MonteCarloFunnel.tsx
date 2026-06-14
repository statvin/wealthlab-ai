// Funil de Monte Carlo: ~100 trajetórias em baixa opacidade (a "nuvem") +
// faixas de percentis P5/P10/P50/P90/P95. Eixo x em anos.

import { useMemo } from 'react'

import type { Funil } from '../api/types'
import { PlotlyChart } from './PlotlyChart'

export function MonteCarloFunnel({ funil }: { funil: Funil }) {
  const data = useMemo(() => {
    const anos = funil.meses.map((m) => m / 12)

    const nuvem = funil.amostra.map((traj) => ({
      x: anos,
      y: traj,
      type: 'scatter',
      mode: 'lines',
      line: { color: 'rgba(52,211,153,0.06)', width: 1 },
      hoverinfo: 'skip',
      showlegend: false,
    }))

    const banda = (chave: string, cor: string, nome: string, largura = 1.2) => ({
      x: anos,
      y: funil.bandas[chave],
      type: 'scatter',
      mode: 'lines',
      line: { color: cor, width: largura },
      name: nome,
      hovertemplate: `${nome}: R$ %{y:,.0f}<extra></extra>`,
    })

    return [
      ...nuvem,
      banda('p95', 'rgba(148,163,184,0.6)', 'P95'),
      banda('p90', 'rgba(96,165,250,0.8)', 'P90'),
      banda('p50', '#34d399', 'P50 (mediana)', 2.6),
      banda('p10', 'rgba(96,165,250,0.8)', 'P10'),
      banda('p5', 'rgba(148,163,184,0.6)', 'P5'),
    ]
  }, [funil])

  return (
    <PlotlyChart
      className="h-80"
      data={data}
      layout={{
        xaxis: { title: 'Anos' },
        yaxis: { title: 'Patrimônio', tickprefix: 'R$ ', tickformat: '.2s' },
      }}
    />
  )
}
