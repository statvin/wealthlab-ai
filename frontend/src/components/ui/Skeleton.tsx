// Bloco de carregamento com a forma do conteúdo (usado na Fase 4).
// Respeita prefers-reduced-motion (só anima em motion-safe).

interface Props {
  className?: string
}

export function Skeleton({ className = '' }: Props) {
  return (
    <div
      aria-hidden="true"
      className={`motion-safe:animate-pulse rounded-lg bg-border ${className}`}
    />
  )
}
