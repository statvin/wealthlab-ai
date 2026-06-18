// Primitivo de número: label (eyebrow) + valor, com variantes de tamanho
// (herói/padrão/pequeno). Tom de cor segue a regra de DADO: neutro por padrão,
// gain/loss apenas quando o número representa ganho/perda. Marca nunca em número.

import type { ReactNode } from 'react'

import { Tooltip } from './Tooltip'

export type StatSize = 'hero' | 'default' | 'sm'
export type StatTone = 'default' | 'gain' | 'loss' | 'muted'

const sizeCls: Record<StatSize, string> = {
  hero: 'text-4xl sm:text-5xl font-semibold tracking-tight',
  default: 'text-2xl font-semibold',
  sm: 'text-lg font-medium',
}

const toneCls: Record<StatTone, string> = {
  default: 'text-content',
  gain: 'text-gain',
  loss: 'text-loss',
  muted: 'text-content-muted',
}

interface Props {
  label: string
  value: ReactNode
  tooltip?: string
  size?: StatSize
  tone?: StatTone
  sub?: ReactNode
}

export function Stat({ label, value, tooltip, size = 'default', tone = 'default', sub }: Props) {
  return (
    <div>
      <div className="flex items-center gap-1.5">
        <span className="eyebrow">{label}</span>
        {tooltip && (
          <Tooltip content={tooltip}>
            <button
              type="button"
              aria-label={`Sobre: ${label}`}
              className="rounded text-content-subtle transition-colors hover:text-content-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
            >
              <InfoIcon />
            </button>
          </Tooltip>
        )}
      </div>
      <div className={`mt-1.5 tnum ${sizeCls[size]} ${toneCls[tone]}`}>{value}</div>
      {sub && <div className="mt-1 text-sm text-content-muted">{sub}</div>}
    </div>
  )
}

function InfoIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </svg>
  )
}
