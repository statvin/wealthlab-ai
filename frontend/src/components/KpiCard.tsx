// KPI com rótulo, valor e tooltip (base/horizonte) — requisito da spec.

interface Props {
  titulo: string
  valor: string
  tooltip?: string
  destaque?: boolean
}

export function KpiCard({ titulo, valor, tooltip, destaque }: Props) {
  return (
    <div className="card">
      <div className="flex items-center gap-1">
        <span className="label">{titulo}</span>
        {tooltip && (
          <span title={tooltip} className="cursor-help text-slate-500" aria-label={tooltip}>
            ⓘ
          </span>
        )}
      </div>
      <div
        className={`mt-1 text-2xl font-semibold ${destaque ? 'text-accent' : 'text-slate-100'}`}
      >
        {valor}
      </div>
    </div>
  )
}
