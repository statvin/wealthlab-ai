// Wrapper React fino sobre o Plotly (build dist-min). Renderiza num <div> via
// Plotly.react e limpa no unmount. Mantemos o tema escuro num layout base e
// fazemos merge raso preservando a grade dos eixos.

import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'

const BASE_LAYOUT = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#cbd5e1', family: 'ui-sans-serif, system-ui, sans-serif' },
  margin: { l: 64, r: 16, t: 16, b: 44 },
  xaxis: { gridcolor: '#27314a', zerolinecolor: '#27314a' },
  yaxis: { gridcolor: '#27314a', zerolinecolor: '#27314a' },
  legend: { orientation: 'h', y: -0.2, font: { size: 11 } },
}

interface Props {
  data: unknown[]
  layout?: Record<string, unknown>
  className?: string
}

export function PlotlyChart({ data, layout, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const merged = {
      ...BASE_LAYOUT,
      ...layout,
      xaxis: { ...BASE_LAYOUT.xaxis, ...(layout?.xaxis as object) },
      yaxis: { ...BASE_LAYOUT.yaxis, ...(layout?.yaxis as object) },
    }
    Plotly.react(el, data, merged, { responsive: true, displayModeBar: false })
  }, [data, layout])

  useEffect(() => {
    const el = ref.current
    return () => {
      if (el) Plotly.purge(el)
    }
  }, [])

  return <div ref={ref} className={className} style={{ width: '100%' }} />
}
