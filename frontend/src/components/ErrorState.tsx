// Estado de erro em linguagem de usuário: diz o que houve e o que fazer, com ação de
// "Tentar novamente". O detalhe técnico (mensagem crua da API) fica atrás de "ver
// detalhes" — sem jargão na superfície, sem pedir desculpa, sem ser vago.

import { useState } from 'react'
import { AlertTriangle, RotateCw } from 'lucide-react'

export function ErrorState({ detalhe, onRetry }: { detalhe: string; onRetry: () => void }) {
  const [verDetalhes, setVerDetalhes] = useState(false)

  return (
    <div className="card flex flex-col items-center gap-3 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-surface-raised text-warning">
        <AlertTriangle size={20} aria-hidden="true" />
      </span>

      <div>
        <p className="text-sm font-medium text-content">Não foi possível rodar a simulação</p>
        <p className="mx-auto mt-1 max-w-sm text-sm text-content-muted">
          Algo deu errado ao calcular sua projeção. Costuma ser temporário — tente de novo.
        </p>
      </div>

      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
      >
        <RotateCw size={16} aria-hidden="true" /> Tentar novamente
      </button>

      <button
        onClick={() => setVerDetalhes((v) => !v)}
        className="rounded text-xs text-content-subtle underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
        aria-expanded={verDetalhes}
      >
        {verDetalhes ? 'Ocultar detalhes' : 'Ver detalhes'}
      </button>

      {verDetalhes && (
        <pre className="mt-1 max-w-full overflow-x-auto rounded-lg bg-surface-raised px-3 py-2 text-left text-xs text-content-muted">
          {detalhe}
        </pre>
      )}
    </div>
  )
}
