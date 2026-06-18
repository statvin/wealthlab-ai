// Histograma dos patrimônios finais (nominais). Usa as bordas/contagens já
// calculadas pelo backend — o front só desenha as barras. Cor do tema atual.

import { useMemo } from 'react'

import type { Histograma } from '../api/types'
import { useTheme } from '../hooks/useTheme'
import { cssRGB } from '../lib/themeColor'
import { PlotlyChart } from './PlotlyChart'

export function FinalHistogram({ histograma }: { histograma: Histograma }) {
  const tema = useTheme()

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
        marker: { color: cssRGB('--brand', 0.55), line: { color: cssRGB('--brand'), width: 0.5 } },
        hovertemplate: 'R$ %{x:,.0f}: %{y} cenários<extra></extra>',
      },
    ]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [histograma, tema])

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
