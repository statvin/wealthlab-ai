// HERO Eclipse: número provável (P50) com count-up, frase-tese, faixa de cenários
// (P10 · IQR · P90), badges e KPIs ancorados na base (mt-auto, p/ fechar a altura da
// coluna de controles). Número neutro; mediana e delta em mint. Glow decorativo no topo.

import { useEffect, useRef, useState, type ReactNode } from 'react'

import type { Resumo, RiskAnalysisOut } from '../api/types'
import { fmtCompactBRL, fmtPct } from '../lib/format'
import type { NivelRuina, Tese } from '../lib/narrative'

// Anima o número exibido até o alvo (easing exponencial). Respeita reduced-motion.
function useCountUp(target: number) {
  const [val, setVal] = useState(target)
  const raf = useRef<number | undefined>(undefined)
  useEffect(() => {
    const reduzir = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduzir || !Number.isFinite(target)) {
      setVal(target)
      return
    }
    const tick = () => {
      setVal((d) => (Math.abs(target - d) <= Math.abs(target) * 0.002 + 1 ? target : d + (target - d) * 0.16))
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current)
    }
  }, [target])
  return val
}

const RUINA_VAL: Record<NivelRuina, string> = {
  baixo: 'text-gain',
  moderado: 'text-warning',
  alto: 'text-loss',
}
const RUINA_BADGE: Record<NivelRuina, string> = {
  baixo: 'bg-gain/[0.12] text-gain',
  moderado: 'bg-warning/[0.15] text-warning',
  alto: 'bg-loss/[0.15] text-loss',
}

export function ResultadoHero({
  resumo,
  risk,
  tese,
  horizonteAnos,
}: {
  resumo: Resumo
  risk: RiskAnalysisOut
  tese: Tese
  horizonteAnos: number
}) {
  const { p10, p50, p90 } = resumo.nominal
  const display = useCountUp(p50)
  const vc95 = risk.var_cvar.find((v) => v.nivel === 0.95)

  // IQR (P25–P75) aproximado a partir dos quantis reais p10/p50/p90 (fit lognormal) —
  // só para a barra; em Fase 3 ligo o P25/P75 real ao backend. clamp em [0,100]%.
  const sigma = p90 > p50 && p50 > 0 ? Math.log(p90 / p50) / 1.2816 : 0
  const p25 = p50 * Math.exp(-0.6745 * sigma)
  const p75 = p50 * Math.exp(0.6745 * sigma)
  const span = Math.max(p90 - p10, 1)
  const clamp = (x: number) => Math.min(Math.max(x, 0), 100)
  const markerPct = clamp(((p50 - p10) / span) * 100)
  const iqLeft = clamp(((p25 - p10) / span) * 100)
  const iqWidth = clamp(((p75 - p25) / span) * 100)

  return (
    <section className="card-hero relative flex flex-col overflow-hidden p-7 sm:p-[30px]">
      <div
        className="pointer-events-none absolute -left-5 -top-[70px] h-[260px] w-[420px]"
        style={{ background: 'radial-gradient(closest-side, rgb(var(--brand) / 0.16), transparent)' }}
        aria-hidden="true"
      />
      <div className="relative flex flex-1 flex-col">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <span className="eyebrow">Resultado da projeção · mediana em {horizonteAnos} anos</span>
          <span className="text-[11.5px] text-content-muted">Cenário base</span>
        </div>

        <div className="mt-3 flex flex-wrap items-baseline gap-x-3.5 gap-y-1">
          <span className="tnum text-[44px] font-semibold leading-none tracking-tight text-content sm:text-[62px]">
            {fmtCompactBRL(display)}
          </span>
          <span className="tnum text-[15px] font-medium text-gain">
            +{fmtCompactBRL(p50 - resumo.patrimonio_inicial)} projetado
          </span>
        </div>

        <p className="mt-4 max-w-[640px] text-[18px] leading-[1.55] text-content-body">{tese.frase}</p>

        <div className="mt-6">
          <div className="relative h-2 rounded-lg bg-brand/[0.12]">
            <div
              className="absolute bottom-0 top-0 rounded-lg bg-brand/30"
              style={{ left: `${iqLeft}%`, width: `${iqWidth}%` }}
              aria-hidden="true"
            />
            <div
              className="absolute -bottom-[5px] -top-[5px] w-[3px] -translate-x-1/2 rounded bg-brand"
              style={{ left: `${markerPct}%`, boxShadow: '0 0 10px rgb(var(--brand) / 0.7)' }}
              aria-hidden="true"
            />
          </div>
          <div className="mt-3 grid grid-cols-3 text-[11.5px]">
            <div>
              <div className="text-content-muted">Pessimista · P10</div>
              <div className="tnum mt-0.5 text-[15px] font-medium text-content">{fmtCompactBRL(p10)}</div>
            </div>
            <div className="text-center">
              <div className="text-content-muted">Central · P50</div>
              <div className="tnum mt-0.5 text-[15px] font-medium text-brand">{fmtCompactBRL(p50)}</div>
            </div>
            <div className="text-right">
              <div className="text-content-muted">Otimista · P90</div>
              <div className="tnum mt-0.5 text-[15px] font-medium text-content">{fmtCompactBRL(p90)}</div>
            </div>
          </div>
        </div>

        <div className="mt-[18px] flex flex-wrap gap-2">
          {tese.metaAtingivelAnos != null ? (
            <Badge className="bg-gain/[0.12] text-gain">Meta atingível em {tese.metaAtingivelAnos} anos</Badge>
          ) : (
            <Badge className="bg-warning/[0.15] text-warning">Meta não atingida no prazo</Badge>
          )}
          <Badge className={RUINA_BADGE[tese.nivelRuina]}>Risco de ruína {tese.nivelRuina}</Badge>
        </div>

        <div className="mt-auto grid grid-cols-3 gap-2 border-t border-border pt-5">
          <Kpi label="VaR 95% · 1 ano" valor={fmtPct(vc95?.var ?? 0)} />
          <Kpi label="Volatilidade a.a." valor={fmtPct(risk.contribuicao.vol_anual_carteira)} />
          <Kpi label="Prob. de ruína" valor={fmtPct(resumo.prob_ruina)} corValor={RUINA_VAL[tese.nivelRuina]} />
        </div>
      </div>
    </section>
  )
}

function Badge({ children, className }: { children: ReactNode; className: string }) {
  return <span className={`rounded-full px-3 py-[5px] text-[12.5px] font-medium ${className}`}>{children}</span>
}

function Kpi({ label, valor, corValor = 'text-content' }: { label: string; valor: string; corValor?: string }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className={`tnum mt-[5px] text-[22px] font-semibold ${corValor}`}>{valor}</div>
    </div>
  )
}
