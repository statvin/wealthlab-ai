// Skeletons com a forma do conteúdo, para a carga inicial (Fase 4). Evitam "texto
// pelado" durante o load — o usuário vê a silhueta do que vai chegar.

import { Skeleton } from './ui/Skeleton'

// Silhueta dos resultados da projeção: herói + insights + um par de gráficos.
export function ResultadosSkeleton() {
  return (
    <div className="space-y-6" aria-hidden="true">
      <div className="card-hero space-y-4">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-10 w-2/5" />
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-2 w-full" />
        <div className="grid grid-cols-3 gap-4 pt-2">
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
          <Skeleton className="h-12" />
        </div>
      </div>

      <div className="card space-y-2">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card space-y-3">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-56" />
        </div>
        <div className="card space-y-3">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-56" />
        </div>
      </div>
    </div>
  )
}

// Silhueta da aba Metodologia: cabeçalho + alguns blocos de texto.
export function MetodologiaSkeleton() {
  return (
    <div className="space-y-6" aria-hidden="true">
      <div className="space-y-2">
        <Skeleton className="h-6 w-56" />
        <Skeleton className="h-3 w-80" />
      </div>
      {[0, 1, 2].map((i) => (
        <div key={i} className="card space-y-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      ))}
    </div>
  )
}
