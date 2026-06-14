// Histograma dos patrimônios finais (nominais). Usa as bordas/contagens já
// calculadas pelo backend — o front só desenha as barras.

import { useMemo } from 'react'

import type { Histograma } from '../api/types'
import { PlotlyChart } from './PlotlyChart'

export function FinalHistogram({ histograma }: { histograma: Histograma }) {
  const data = useMemo(() => {
    const { edges, counts } = histograma
    const centros = counts.map((_, i) => (edges[i] + edges[i + 1]) / 2)
    const larguras = counts.map((_, i) => edges[i + 1] - edges[i])
    return [
      {
        x: centros,
        y: counts,
        width: larguras,
        type: 'bar',
        marker: { color: 'rgba(52,211,153,0.6)', line: { color: '#34d399', width: 0.5 } },
        hovertemplate: 'R$ %{x:,.0f}: %{y} cenários<extra></extra>',
      },
    ]
  }, [histograma])

  return (
    <PlotlyChart
      className="h-72"
      data={data}
      layout={{
        bargap: 0.02,
        xaxis: { title: 'Patrimônio final', tickprefix: 'R$ ', tickformat: '.2s' },
        yaxis: { title: 'Cenários' },
      }}
    />
  )
}
