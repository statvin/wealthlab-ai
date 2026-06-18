// Sidebar de parâmetros da SIMULAÇÃO (não da composição da carteira).

import type { RebalanceMode } from '../api/types'
import type { SimInputs } from '../hooks/useSimulation'
import { NumberField } from './NumberField'

const inputCls =
  'w-full rounded-lg border border-border bg-canvas px-3 py-2 text-sm text-content focus:border-brand focus:outline-none'

interface Props {
  inputs: SimInputs
  onChange: (i: SimInputs) => void
  onRun: () => void
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
      <span className="label">{label}</span>
      <NumberField value={value} onChange={onChange} step={step} className={`mt-1 ${inputCls}`} />
    </label>
  )
}

export function Sidebar({ inputs, onChange, onRun, loading }: Props) {
  const set = <K extends keyof SimInputs>(k: K, v: SimInputs[K]) =>
    onChange({ ...inputs, [k]: v })

  return (
    <aside className="flex w-full flex-col gap-3 lg:h-full lg:w-72 lg:shrink-0">
      <h2 className="text-sm font-semibold text-content-body">Parâmetros</h2>

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
      <Campo label="Prazo da meta (anos)" value={inputs.prazoMetaAnos} onChange={(v) => set('prazoMetaAnos', v)} />
      <Campo label="Nº de cenários" value={inputs.nCenarios} step="1000" onChange={(v) => set('nCenarios', v)} />
      <Campo label="df (t-Student, cauda)" value={inputs.df} onChange={(v) => set('df', v)} />
      <Campo label="Seed" value={inputs.seed} onChange={(v) => set('seed', v)} />

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

      <button
        onClick={onRun}
        disabled={loading}
        className="mt-2 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? 'Rodando…' : 'Rodar simulação'}
      </button>
    </aside>
  )
}
