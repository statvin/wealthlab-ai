// Passo 1 do fluxo: os campos da simulação ficam VISÍVEIS no topo (não mais
// escondidos atrás de um botão). Carteira como resumo + "editar"; ajustes
// técnicos recolhidos em "avançados".

import { useState } from 'react'

import type { HoldingDTO, RebalanceMode } from '../api/types'
import type { SimInputs } from '../hooks/useSimulation'
import { fmtPct } from '../lib/format'
import { pesosPorAtivo } from '../lib/portfolio'
import { NumberField } from './NumberField'

const inputCls =
  'w-full rounded-lg border border-border bg-canvas px-3 py-2 text-sm text-content focus:border-brand focus:outline-none'

interface Props {
  holdings: HoldingDTO[]
  inputs: SimInputs
  onChange: (i: SimInputs) => void
  onRun: () => void
  onEditCarteira: () => void
  loading: boolean
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
      <span className="mb-1.5 block text-xs text-content-muted">{label}</span>
      <NumberField value={value} onChange={onChange} step={step} className={inputCls} />
    </label>
  )
}

export function SimulationInputs({ holdings, inputs, onChange, onRun, onEditCarteira, loading }: Props) {
  const [avancado, setAvancado] = useState(false)
  const set = <K extends keyof SimInputs>(k: K, v: SimInputs[K]) => onChange({ ...inputs, [k]: v })
  const pesos = pesosPorAtivo(holdings)

  return (
    <section className="card">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h2 className="text-sm font-semibold text-content">Configurar a simulação</h2>
        <p className="text-xs text-content-muted">
          Carteira:{' '}
          {pesos.map((p) => `${p.ticker} ${fmtPct(p.peso, 0)}`).join(' · ')}{' '}
          <button
            onClick={onEditCarteira}
            className="text-brand transition-colors hover:text-brand-strong focus:outline-none focus-visible:underline"
          >
            · editar
          </button>
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Campo label="Horizonte (anos)" value={inputs.horizonteAnos} onChange={(v) => set('horizonteAnos', v)} />
        <Campo label="Aporte mensal (R$)" value={inputs.aporteMensal} step="100" onChange={(v) => set('aporteMensal', v)} />
        <Campo label="Saque mensal (R$)" value={inputs.saqueMensal} step="100" onChange={(v) => set('saqueMensal', v)} />
        <Campo
          label="Inflação a.a. (%)"
          value={Number((inputs.inflacaoAa * 100).toFixed(2))}
          step="0.5"
          onChange={(v) => set('inflacaoAa', v / 100)}
        />
        <Campo label="Meta (R$)" value={inputs.valorMeta} step="50000" onChange={(v) => set('valorMeta', v)} />
        <label className="block">
          <span className="mb-1.5 block text-xs text-content-muted">Rebalanceamento</span>
          <select
            value={inputs.rebalanceamento}
            onChange={(e) => set('rebalanceamento', e.target.value as RebalanceMode)}
            className={inputCls}
          >
            <option value="ANUAL_AO_ALVO">Anual ao alvo</option>
            <option value="NENHUM">Buy &amp; hold</option>
          </select>
        </label>
      </div>

      {avancado && (
        <div className="mt-4 grid grid-cols-2 gap-4 border-t border-border pt-4 sm:grid-cols-3">
          <Campo label="Prazo da meta (anos)" value={inputs.prazoMetaAnos} onChange={(v) => set('prazoMetaAnos', v)} />
          <Campo label="Nº de cenários" value={inputs.nCenarios} step="1000" onChange={(v) => set('nCenarios', v)} />
          <Campo label="df (t-Student, cauda)" value={inputs.df} onChange={(v) => set('df', v)} />
          <Campo label="Seed" value={inputs.seed} onChange={(v) => set('seed', v)} />
        </div>
      )}

      <div className="mt-5 flex items-center justify-between gap-3">
        <button
          onClick={() => setAvancado((a) => !a)}
          className="text-xs text-content-muted transition-colors hover:text-content focus:outline-none focus-visible:underline"
        >
          {avancado ? 'Ocultar' : 'Mostrar'} ajustes avançados
        </button>
        <button
          onClick={onRun}
          disabled={loading}
          className="rounded-lg bg-brand px-5 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50"
        >
          {loading ? 'Rodando…' : 'Rodar simulação'}
        </button>
      </div>
    </section>
  )
}
