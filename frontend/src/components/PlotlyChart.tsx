// Wrapper React do Plotly (dist-min). O layout (fundo, fonte, grade) é montado a
// partir das CSS variables do tema atual e re-renderiza ao alternar claro/escuro.
// Grade discreta e sem barra de modo — gráfico editorial, não terminal.

import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'

import { useTheme } from '../hooks/useTheme'
import { cssRGB } from '../lib/themeColor'

interface Props {
  data: unknown[]
  layout?: Record<string, unknown>
  className?: string
}

export function PlotlyChart({ data, layout, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const tema = useTheme() // dispara re-render ao trocar de tema

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const eixo = {
      gridcolor: cssRGB('--border', 0.6),
      zerolinecolor: cssRGB('--border'),
      linecolor: cssRGB('--border'),
      tickfont: { color: cssRGB('--content-muted') },
      // Reserva espaço p/ ticks + título do eixo (evita o título vertical colar nos valores).
      automargin: true,
    }
    const base = {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {
        color: cssRGB('--content-muted'),
        family: 'Inter Variable, ui-sans-serif, system-ui, sans-serif',
        size: 12,
      },
      margin: { l: 64, r: 16, t: 16, b: 44 },
      xaxis: { ...eixo },
      yaxis: { ...eixo },
      legend: { orientation: 'h', y: -0.2, font: { size: 11 } },
    }
    // Afasta o título de cada eixo dos rótulos de tick (standoff). Com automargin,
    // a margem cresce para acomodar — nada é cortado.
    const comStandoff = (ax: Record<string, unknown>, standoff: number) =>
      ax.title == null
        ? ax
        : {
            ...ax,
            title: { standoff, ...(typeof ax.title === 'string' ? { text: ax.title } : (ax.title as object)) },
          }
    const merged = {
      ...base,
      ...layout,
      xaxis: comStandoff({ ...base.xaxis, ...(layout?.xaxis as object) }, 10),
      yaxis: comStandoff({ ...base.yaxis, ...(layout?.yaxis as object) }, 16),
    }
    Plotly.react(el, data, merged, { responsive: true, displayModeBar: false })
  }, [data, layout, tema])

  useEffect(() => {
    const el = ref.current
    return () => {
      if (el) Plotly.purge(el)
    }
  }, [])

  return <div ref={ref} className={className} style={{ width: '100%' }} />
}
