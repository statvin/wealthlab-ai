// Passo 2: o resultado da projeção. Número provável (neutro) + delta (verde) +
// frase-tese + faixa de cenários (P10–P90, marcador em P50 na posição real) +
// tira de métricas. Tudo em grid alinhado — sem texto flutuante.

import type { RiskAnalysisOut } from '../api/types'
import type { Resumo } from '../api/types'
import { fmtCompactBRL, fmtPct } from '../lib/format'
import type { NivelRuina, Tese } from '../lib/narrative'
import { Badge, type BadgeTone } from './ui/Badge'
import { Stat } from './ui/Stat'

const RUINA_TONE: Record<NivelRuina, BadgeTone> = {
  baixo: 'success',
  moderado: 'warning',
  alto: 'danger',
}

export function ResultadoHero({
  resumo,
  risk,
  tese,
}: {
  resumo: Resumo
  risk: RiskAnalysisOut
  tese: Tese
}) {
  const { p10, p50, p90 } = resumo.nominal
  // Posição do marcador P50 dentro da faixa P10–P90 (revela a assimetria).
  const pos = p90 > p10 ? Math.min(Math.max((p50 - p10) / (p90 - p10), 0), 1) * 100 : 50
  const vc95 = risk.var_cvar.find((v) => v.nivel === 0.95)

  return (
    <section className="card-hero">
      <p className="eyebrow mb-3">Resultado da projeção</p>

      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <span className="tnum text-4xl font-semibold tracking-tight text-content sm:text-5xl">
          {fmtCompactBRL(p50)}
        </span>
        <span className="tnum text-sm text-gain">
          +{fmtCompactBRL(p50 - resumo.patrimonio_inicial)} projetado
        </span>
      </div>

      <p className="mt-4 max-w-2xl text-lg leading-relaxed text-content sm:text-xl">{tese.frase}</p>

      {/* Faixa de cenários. */}
      <div className="mt-7">
        <div className="relative h-2 rounded-full bg-brand/15">
          <span
            className="absolute -top-1 h-4 w-[3px] -translate-x-1/2 rounded bg-brand"
            style={{ left: `${pos}%` }}
            aria-hidden="true"
          />
        </div>
        <div className="mt-3 grid grid-cols-3 text-xs">
          <div>
            <div className="text-content-muted">Pessimista (P10)</div>
            <div className="tnum text-sm text-content">{fmtCompactBRL(p10)}</div>
          </div>
          <div className="text-center">
            <div className="text-content-muted">Central (P50)</div>
            <div className="tnum text-sm text-content">{fmtCompactBRL(p50)}</div>
          </div>
          <div className="text-right">
            <div className="text-content-muted">Otimista (P90)</div>
            <div className="tnum text-sm text-content">{fmtCompactBRL(p90)}</div>
          </div>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {tese.metaAtingivelAnos != null && (
          <Badge tone="success">Meta atingível em {tese.metaAtingivelAnos} anos</Badge>
        )}
        <Badge tone={RUINA_TONE[tese.nivelRuina]}>Risco de ruína {tese.nivelRuina}</Badge>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 border-t border-border pt-5">
        <Stat
          size="sm"
          label="VaR 95% (1 ano)"
          value={fmtPct(vc95?.var ?? 0)}
          tooltip="Perda máxima esperada em 1 ano com 95% de confiança (risco de mercado)."
        />
        <Stat
          size="sm"
          label="Volatilidade anual"
          value={fmtPct(risk.contribuicao.vol_anual_carteira)}
          tooltip="Volatilidade anualizada da carteira (a renda variável domina)."
        />
        <Stat
          size="sm"
          label="Prob. de ruína"
          value={fmtPct(resumo.prob_ruina)}
          tooltip="Fração de cenários que tocam zero antes do fim do horizonte."
        />
      </div>
    </section>
  )
}
