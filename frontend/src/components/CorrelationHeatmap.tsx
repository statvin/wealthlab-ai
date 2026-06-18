// Heatmap da correlação estimada da renda variável. (RF não tem correlação no
// modelo base, então só os ativos de RV aparecem.)

import { useMemo } from 'react'

import type { Correlacao } from '../api/types'
import { PlotlyChart } from './PlotlyChart'

export function CorrelationHeatmap({ correlacao }: { correlacao: Correlacao }) {
  const data = useMemo(() => {
    const texto = correlacao.matriz.map((linha) => linha.map((v) => v.toFixed(2)))
    return [
      {
        z: correlacao.matriz,
        x: correlacao.labels,
        y: correlacao.labels,
        type: 'heatmap',
        zmin: -1,
        zmax: 1,
        colorscale: 'RdBu',
        reversescale: true,
        text: texto,
        texttemplate: '%{text}',
        textfont: { size: 12 },
        hovertemplate: '%{y} × %{x}: %{z:.2f}<extra></extra>',
        colorbar: { thickness: 10, len: 0.9 },
      },
    ]
  }, [correlacao])

  if (correlacao.labels.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-content-subtle">
        Sem ativos de renda variável para correlacionar.
      </div>
    )
  }

  return (
    <PlotlyChart
      className="h-72"
      data={data}
      layout={{ margin: { l: 90, r: 16, t: 16, b: 70 } }}
    />
  )
}
