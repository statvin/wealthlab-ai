// Pílula semântica (ex.: "Meta atingível em 14 anos"). Sempre via token de cor.

import type { ReactNode } from 'react'

export type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'accent'

const toneCls: Record<BadgeTone, string> = {
  neutral: 'border-ink-600 bg-ink-700/40 text-slate-300',
  success: 'border-semantic-success/30 bg-semantic-success/10 text-semantic-success',
  warning: 'border-semantic-warning/30 bg-semantic-warning/10 text-semantic-warning',
  danger: 'border-semantic-danger/30 bg-semantic-danger/10 text-semantic-danger',
  info: 'border-semantic-info/30 bg-semantic-info/10 text-semantic-info',
  accent: 'border-accent/30 bg-accent/10 text-accent',
}

interface Props {
  children: ReactNode
  tone?: BadgeTone
}

export function Badge({ children, tone = 'neutral' }: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${toneCls[tone]}`}
    >
      {children}
    </span>
  )
}
