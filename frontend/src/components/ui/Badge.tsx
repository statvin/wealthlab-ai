// Pílula semântica (ex.: "Meta atingível em 14 anos"). Sempre via token de cor.

import type { ReactNode } from 'react'

export type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info' | 'brand'

const toneCls: Record<BadgeTone, string> = {
  neutral: 'border-border bg-canvas text-content-body',
  success: 'border-gain/30 bg-gain/10 text-gain',
  warning: 'border-warning/30 bg-warning/10 text-warning',
  danger: 'border-loss/30 bg-loss/10 text-loss',
  info: 'border-info/30 bg-info/10 text-info',
  brand: 'border-brand/30 bg-brand/10 text-brand',
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
