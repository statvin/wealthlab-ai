// "Posso me aposentar aos X?" — acumulação até a aposentadoria e decumulação
// (saques) até a idade final. Mostra prob. de sucesso, patrimônio na
// aposentadoria e o saque mensal sustentável.

import { useState } from 'react'

import { useRetirement } from '../hooks/useRetirement'
import { fmtCompactBRL, fmtPct } from '../lib/format'
import { NumberField } from './NumberField'
import { Stat } from './ui/Stat'

const inputCls =
  'w-full rounded-lg border border-border bg-canvas px-3 py-2 text-sm text-content focus:border-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/50'

const PADRAO = {
  idade_atual: 35,
  idade_aposentadoria: 60,
  idade_final: 90,
  aporte_mensal: 2000,
  saque_mensal_desejado: 8000,
  alvo_sucesso: 0.9,
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

export function RetirementPanel({ simId }: { simId: number | null }) {
  const [f, setF] = useState(PADRAO)
  const { loading, error, data, run } = useRetirement(simId)
  const set = <K extends keyof typeof f>(k: K, v: number) => setF({ ...f, [k]: v })

  if (simId == null) {
    return (
      <div className="card text-sm text-content-muted">
        Rode uma simulação primeiro (aba Dashboard) — a análise de aposentadoria usa a sua carteira.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <h3 className="mb-1 text-sm font-semibold text-content-body">Posso me aposentar?</h3>
        <p className="mb-3 text-xs text-content-subtle">
          Acumula com aportes até a aposentadoria e depois sustenta os saques até a idade final,
          sobre a carteira atual.
        </p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <Campo label="Idade atual" value={f.idade_atual} onChange={(v) => set('idade_atual', v)} />
          <Campo label="Aposentar aos" value={f.idade_aposentadoria} onChange={(v) => set('idade_aposentadoria', v)} />
          <Campo label="Idade final" value={f.idade_final} onChange={(v) => set('idade_final', v)} />
          <Campo label="Aporte mensal (R$)" value={f.aporte_mensal} step="100" onChange={(v) => set('aporte_mensal', v)} />
          <Campo label="Saque desejado (R$)" value={f.saque_mensal_desejado} step="100" onChange={(v) => set('saque_mensal_desejado', v)} />
          <Campo label="Sucesso alvo (0–1)" value={f.alvo_sucesso} step="0.05" onChange={(v) => set('alvo_sucesso', v)} />
        </div>
        <button
          onClick={() => run(f)}
          disabled={loading}
          className="mt-3 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50"
        >
          {loading ? 'Calculando…' : 'Analisar aposentadoria'}
        </button>
        {error && <p className="mt-2 text-sm text-loss">{error}</p>}
      </div>

      {data && (
        <div className="card grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat
            label="Prob. de sucesso"
            value={fmtPct(data.prob_sucesso)}
            tone="gain"
            tooltip="Fração dos cenários em que o dinheiro dura até a idade final com o saque desejado."
          />
          <Stat
            label="Saque sustentável"
            value={fmtCompactBRL(data.saque_sustentavel)}
            tooltip={`Maior saque mensal com sucesso ≥ ${fmtPct(data.alvo_sucesso, 0)}.`}
          />
          <Stat
            label="Patrimônio ao aposentar"
            value={fmtCompactBRL(data.patrimonio_aposentadoria.p50)}
            tooltip="Mediana do patrimônio no momento da aposentadoria."
          />
          <Stat
            label="Patrimônio final (P50)"
            value={fmtCompactBRL(data.patrimonio_final.p50)}
            tooltip="Mediana do patrimônio na idade final, após os saques."
          />
        </div>
      )}
    </div>
  )
}
