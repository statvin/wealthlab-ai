// Funil de Monte Carlo: ~100 trajetórias em baixa opacidade (a "nuvem") +
// faixas de percentis P5/P10/P50/P90/P95. Eixo x em anos. Cores do tema atual.

import { useMemo } from 'react'

import type { Funil } from '../api/types'
import { useTheme } from '../hooks/useTheme'
import { cssRGB } from '../lib/themeColor'
import { PlotlyChart } from './PlotlyChart'

export function MonteCarloFunnel({ funil }: { funil: Funil }) {
  const tema = useTheme()

  const data = useMemo(() => {
    const anos = funil.meses.map((m) => m / 12)
    const corNuvem = cssRGB('--brand', 0.08)
    const corP50 = cssRGB('--brand')
    const corMeio = cssRGB('--info', 0.85)
    const corExtremo = cssRGB('--content-subtle', 0.7)

    const nuvem = funil.amostra.map((traj) => ({
      x: anos,
      y: traj,
      type: 'scatter',
      mode: 'lines',
      line: { color: corNuvem, width: 1 },
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
      banda('p95', corExtremo, 'P95'),
      banda('p90', corMeio, 'P90'),
      banda('p50', corP50, 'P50 (mediana)', 2.6),
      banda('p10', corMeio, 'P10'),
      banda('p5', corExtremo, 'P5'),
    ]
    // recomputa as cores ao trocar de tema
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [funil, tema])

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
