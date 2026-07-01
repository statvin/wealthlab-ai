// Trajetória do patrimônio (Eclipse): SVG bespoke sobre o funil REAL do Monte Carlo.
// Escala Y logarítmica, bandas P5–P95 e P25–P75, 3 trajetórias-amostra, linha de meta,
// mediana com animação de traçado (na 1ª aparição) e hover com guia + tooltip.
// P25/P75 são aproximados dos quantis reais (fit lognormal) até o backend fornecê-los.

import { useMemo, useState, type CSSProperties, type MouseEvent, type ReactNode } from 'react'

import type { Funil } from '../api/types'
import { fmtCompactBRL } from '../lib/format'

const VB_W = 880
const X0 = 64
const X1 = 864
const Y_TOP = 22
const Y_BOT = 296
const TICKS = [1e5, 2.5e5, 5e5, 1e6, 2e6, 4e6, 8e6, 1.6e7, 3.2e7]

export function TrajectoryChart({
  funil,
  meta,
  horizonteAnos,
}: {
  funil: Funil
  meta: number
  horizonteAnos: number
}) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null)

  const g = useMemo(() => {
    const { p5, p10, p50, p90, p95 } = funil.bandas
    const N = p50.length
    const anos = funil.meses.map((m) => m / 12)
    const T = anos[N - 1] || horizonteAnos || 1
    const W0 = p50[0] ?? 1

    // P25/P75 aproximados por mês (fit lognormal a partir de p10/p50/p90).
    const sig = p50.map((m, i) => {
      if (m <= 0) return 0
      const a = p90[i] > m ? Math.log(p90[i] / m) : 0
      const b = m > p10[i] && p10[i] > 0 ? Math.log(m / p10[i]) : 0
      return (a + b) / (2 * 1.2816)
    })
    const p25 = p50.map((m, i) => m * Math.exp(-0.6745 * sig[i]))
    const p75 = p50.map((m, i) => m * Math.exp(0.6745 * sig[i]))

    const vmax = Math.max(p95[N - 1], meta) * 1.1
    const vmin = Math.max(1, Math.min(W0 * 0.5, p5[N - 1] * 0.85))
    const L = Math.log
    const yOf = (v: number) =>
      Y_TOP + (1 - (L(Math.max(v, vmin)) - L(vmin)) / (L(vmax) - L(vmin))) * (Y_BOT - Y_TOP)
    const xOf = (i: number) => X0 + (anos[i] / T) * (X1 - X0)

    const line = (arr: number[]) => arr.map((v, i) => `${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`)
    const bandPath = (up: number[], lo: number[]) =>
      `M ${line(up).join(' L ')} L ${line(lo).reverse().join(' L ')} Z`
    const trajPath = (arr: number[]) => `M ${line(arr).join(' L ')}`

    const a = funil.amostra
    const sample = a.length
      ? [...new Set([0, Math.floor(a.length / 2), a.length - 1])].map((k) => trajPath(a[k]))
      : []

    const ticks = TICKS.filter((v) => v > vmin * 1.02 && v < vmax * 0.98).map((v) => ({ v, y: yOf(v) }))

    return {
      N,
      anos,
      p10,
      p50,
      p90,
      xOf,
      yOf,
      pOuter: bandPath(p95, p5),
      pInner: bandPath(p75, p25),
      pMedian: trajPath(p50),
      sample,
      yMeta: meta > vmin && meta < vmax ? yOf(meta) : null,
      medEndY: yOf(p50[N - 1]),
      ticks,
    }
  }, [funil, meta, horizonteAnos])

  const hi = hoverIdx != null && hoverIdx < g.N ? hoverIdx : null
  const hx = hi != null ? g.xOf(hi) : 0
  const anosH = hi != null ? g.anos[hi] : 0
  const leftPct = (hx / VB_W) * 100
  const side: 'left' | 'right' = leftPct > 60 ? 'right' : 'left'

  const onMove = (e: MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    const vbX = ((e.clientX - r.left) / r.width) * VB_W
    const frac = (vbX - X0) / (X1 - X0)
    const idx = Math.round(Math.min(Math.max(frac, 0), 1) * (g.N - 1))
    if (idx !== hoverIdx) setHoverIdx(idx)
  }

  const tooltipStyle: CSSProperties =
    side === 'left'
      ? { left: `${leftPct}%`, marginLeft: 14, boxShadow: '0 10px 30px -8px rgba(0,0,0,.6)' }
      : { right: `${100 - leftPct}%`, marginRight: 14, boxShadow: '0 10px 30px -8px rgba(0,0,0,.6)' }

  return (
    <section className="card p-[22px]">
      <div className="mb-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-[15px] font-semibold text-content">Trajetória do patrimônio</div>
          <div className="mt-0.5 text-[12.5px] text-content-muted">
            Percentis do funil de Monte Carlo · horizonte de {horizonteAnos} anos
          </div>
        </div>
        <div className="flex flex-wrap gap-3.5 text-[11.5px] text-content-body">
          <Leg swatch={<span className="h-2 w-3.5 rounded-sm bg-brand/[0.14]" />}>P5–P95</Leg>
          <Leg swatch={<span className="h-2 w-3.5 rounded-sm bg-brand/30" />}>P25–P75</Leg>
          <Leg swatch={<span className="h-0.5 w-3.5 bg-brand" />}>Mediana</Leg>
          <Leg swatch={<span className="w-3.5 border-t border-dashed border-content-muted" />}>
            Meta {fmtCompactBRL(meta)}
          </Leg>
        </div>
      </div>

      <div className="relative" onMouseMove={onMove} onMouseLeave={() => setHoverIdx(null)}>
        <svg className="wlchart block overflow-visible" viewBox={`0 0 ${VB_W} 340`} width="100%">
          {g.ticks.map(({ v, y }) => (
            <g key={v}>
              <line x1={X0} y1={y} x2={X1} y2={y} stroke="rgb(var(--hairline))" strokeWidth={1} />
              <text
                x={X0 - 8}
                y={y + 3.5}
                textAnchor="end"
                fontSize={10.5}
                fill="rgb(var(--content-subtle))"
              >
                {fmtCompactBRL(v)}
              </text>
            </g>
          ))}
          <path d={g.pOuter} fill="rgb(var(--brand) / 0.08)" />
          <path d={g.pInner} fill="rgb(var(--brand) / 0.18)" />
          {g.sample.map((d, i) => (
            <path key={i} d={d} fill="none" stroke="rgb(var(--brand) / 0.22)" strokeWidth={1} />
          ))}
          {g.yMeta != null && (
            <line
              x1={X0}
              y1={g.yMeta}
              x2={X1}
              y2={g.yMeta}
              stroke="rgb(var(--content-muted))"
              strokeWidth={1}
              strokeDasharray="4 4"
            />
          )}
          <path
            className="wldraw"
            d={g.pMedian}
            fill="none"
            stroke="rgb(var(--brand))"
            strokeWidth={2.5}
            strokeDasharray={2400}
            style={{ animation: 'wldraw 1.1s ease' }}
          />
          <circle cx={X1} cy={g.medEndY} r={4.5} fill="rgb(var(--brand))" />
          {hi != null && (
            <g>
              <line x1={hx} y1={Y_TOP} x2={hx} y2={Y_BOT} stroke="rgb(var(--brand) / 0.45)" strokeWidth={1} />
              <circle cx={hx} cy={g.yOf(g.p50[hi])} r={4} fill="rgb(var(--brand))" />
            </g>
          )}
        </svg>

        {hi != null && (
          <div
            className="pointer-events-none absolute top-1.5 rounded-[9px] border border-border bg-surface-raised px-3 py-2"
            style={tooltipStyle}
          >
            <div className="mb-1 text-[11px] text-content-muted">
              {anosH < 0.5 ? 'Hoje' : `Ano ${Math.round(anosH)}`}
            </div>
            <div className="flex gap-3.5">
              <Tt label="P90" cor="text-content-body" v={fmtCompactBRL(g.p90[hi])} />
              <Tt label="P50" cor="text-brand" v={fmtCompactBRL(g.p50[hi])} />
              <Tt label="P10" cor="text-content-body" v={fmtCompactBRL(g.p10[hi])} />
            </div>
          </div>
        )}
      </div>

      <div className="mt-1.5 flex justify-between pl-12 text-[11.5px] text-content-muted">
        <span>Hoje</span>
        <span>{Math.round(horizonteAnos / 3)} anos</span>
        <span>{Math.round((2 * horizonteAnos) / 3)} anos</span>
        <span>{horizonteAnos} anos</span>
      </div>
    </section>
  )
}

function Leg({ swatch, children }: { swatch: ReactNode; children: ReactNode }) {
  return <span className="inline-flex items-center gap-1.5">{swatch}{children}</span>
}

function Tt({ label, cor, v }: { label: string; cor: string; v: string }) {
  return (
    <div>
      <div className="text-[10px] text-content-muted">{label}</div>
      <div className={`tnum text-[13px] font-semibold ${cor}`}>{v}</div>
    </div>
  )
}
