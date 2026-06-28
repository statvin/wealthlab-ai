// Controles Eclipse: sliders Horizonte/Aporte (o App recalcula ao vivo via debounce),
// carteira (resumo + "editar"), ajustes avançados recolhidos e CTA com glow. Mantém a
// mesma API de props do componente anterior.

import { useState } from 'react'

import type { HoldingDTO, RebalanceMode } from '../api/types'
import type { SimInputs } from '../hooks/useSimulation'
import { fmtPct } from '../lib/format'
import { pesosPorAtivo } from '../lib/portfolio'
import { NumberField } from './NumberField'

// Cores dos ativos na lista da carteira (cicla quando há mais ativos).
const PALETA = ['#2BE8A5', '#5BC8F5', '#F5A623', '#9AA0AC', '#C084FC', '#F472B6']

const inputCls =
  'w-full rounded-lg border border-border bg-canvas px-3 py-2 text-sm text-content focus:border-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/50'

const brl0 = (v: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)

interface Props {
  holdings: HoldingDTO[]
  inputs: SimInputs
  onChange: (i: SimInputs) => void
  onRun: () => void
  onEditCarteira: () => void
  loading: boolean
}

export function SimulationInputs({ holdings, inputs, onChange, onRun, onEditCarteira, loading }: Props) {
  const [avancado, setAvancado] = useState(false)
  const set = <K extends keyof SimInputs>(k: K, v: SimInputs[K]) => onChange({ ...inputs, [k]: v })
  const pesos = pesosPorAtivo(holdings)

  return (
    <section className="card flex flex-col p-[22px]">
      <div className="eyebrow mb-[18px]">Configurar simulação</div>

      <SliderRow
        label="Horizonte"
        valor={`${inputs.horizonteAnos} anos`}
        min={5}
        max={40}
        step={1}
        value={inputs.horizonteAnos}
        onChange={(v) => set('horizonteAnos', v)}
      />
      <SliderRow
        label="Aporte mensal"
        valor={`${brl0(inputs.aporteMensal)}/mês`}
        min={0}
        max={10000}
        step={250}
        value={inputs.aporteMensal}
        onChange={(v) => set('aporteMensal', v)}
      />

      <div className="mt-1 border-t border-border pt-[18px]">
        <div className="mb-2.5 flex items-baseline justify-between">
          <span className="text-[11.5px] text-content-muted">Carteira</span>
          <button
            onClick={onEditCarteira}
            className="rounded text-[11.5px] text-brand transition-colors hover:text-brand-strong focus:outline-none focus-visible:underline"
          >
            editar
          </button>
        </div>
        <div className="flex flex-col gap-[7px]">
          {pesos.map((p, i) => (
            <div key={p.ticker} className="flex items-center gap-2.5">
              <span
                className="h-2 w-2 shrink-0 rounded-sm"
                style={{ background: PALETA[i % PALETA.length] }}
                aria-hidden="true"
              />
              <span className="flex-1 truncate text-[13px] text-content-body">{p.ticker}</span>
              <span className="tnum text-[13px] font-semibold text-content">{fmtPct(p.peso, 0)}</span>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={() => setAvancado((a) => !a)}
        className="mt-4 self-start rounded text-[11.5px] text-content-muted transition-colors hover:text-content-body focus:outline-none focus-visible:underline"
      >
        {avancado ? 'Ocultar' : 'Mostrar'} ajustes avançados
      </button>
      {avancado && (
        <div className="mt-3 grid grid-cols-2 gap-3 border-t border-border pt-3">
          <Campo label="Saque mensal (R$)" value={inputs.saqueMensal} step="100" onChange={(v) => set('saqueMensal', v)} />
          <Campo
            label="Inflação a.a. (%)"
            value={Number((inputs.inflacaoAa * 100).toFixed(2))}
            step="0.5"
            onChange={(v) => set('inflacaoAa', v / 100)}
          />
          <Campo label="Meta (R$)" value={inputs.valorMeta} step="50000" onChange={(v) => set('valorMeta', v)} />
          <label className="block">
            <span className="label">Rebalanceamento</span>
            <select
              value={inputs.rebalanceamento}
              onChange={(e) => set('rebalanceamento', e.target.value as RebalanceMode)}
              className={`mt-1 ${inputCls}`}
            >
              <option value="ANUAL_AO_ALVO">Anual ao alvo</option>
              <option value="NENHUM">Buy &amp; hold</option>
            </select>
          </label>
          <Campo label="Nº de cenários" value={inputs.nCenarios} step="1000" onChange={(v) => set('nCenarios', v)} />
          <Campo label="Seed" value={inputs.seed} onChange={(v) => set('seed', v)} />
        </div>
      )}

      <button
        onClick={onRun}
        disabled={loading}
        className="mt-[22px] w-full rounded-[10px] bg-brand px-3 py-[11px] text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-60"
        style={{ boxShadow: '0 0 24px -6px rgb(var(--brand) / 0.5)' }}
      >
        {loading ? 'Rodando…' : 'Rodar simulação'}
      </button>
    </section>
  )
}

function SliderRow({
  label,
  valor,
  min,
  max,
  step,
  value,
  onChange,
}: {
  label: string
  valor: string
  min: number
  max: number
  step: number
  value: number
  onChange: (v: number) => void
}) {
  return (
    <div className="mb-5">
      <div className="mb-[9px] flex items-baseline justify-between">
        <span className="text-[13px] text-content-body">{label}</span>
        <span className="tnum text-sm font-semibold text-content">{valor}</span>
      </div>
      <input
        type="range"
        className="wlrange"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={label}
      />
    </div>
  )
}

function Campo({
  label,
  value,
  onChange,
  step,
}: {
  label: string
  value: number
  onChange: (v: number) => void
  step?: string
}) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      <NumberField value={value} onChange={onChange} step={step} className={`mt-1 ${inputCls}`} />
    </label>
  )
}
