// Tooltip acessível (Radix) — substitui o `title=` nativo e o glifo ⓘ.
// Operável por teclado, com foco visível no gatilho.

import * as RadixTooltip from '@radix-ui/react-tooltip'
import type { ReactNode } from 'react'

interface Props {
  content: ReactNode
  children: ReactNode
}

export function Tooltip({ content, children }: Props) {
  return (
    <RadixTooltip.Provider delayDuration={150} skipDelayDuration={300}>
      <RadixTooltip.Root>
        <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            sideOffset={6}
            collisionPadding={8}
            className="z-50 max-w-xs rounded-lg border border-border bg-surface-raised px-3 py-2 text-xs leading-relaxed text-content-body shadow-xl shadow-black/10"
          >
            {content}
            <RadixTooltip.Arrow className="fill-surface-raised" />
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  )
}
