// Primeiro contato. Em vez de despejar números sobre a carteira-exemplo na primeira
// visita, explica o que o produto faz e deixa o usuário escolher: rodar o exemplo ou
// montar a própria carteira. Aparece só até o primeiro CTA (gate por localStorage no App).

import { Pencil, Play } from 'lucide-react'

import type { HoldingDTO } from '../api/types'

export function WelcomePanel({
  holdings,
  onRunExample,
  onEditPortfolio,
}: {
  holdings: HoldingDTO[]
  onRunExample: () => void
  onEditPortfolio: () => void
}) {
  return (
    <section className="card-hero mx-auto max-w-2xl text-center">
      <p className="eyebrow mb-4">
        <span className="font-semibold text-brand">WealthLab</span>{' '}
        <span className="font-light text-content-muted">AI</span>
      </p>

      <h1 className="text-2xl font-semibold tracking-tight text-content sm:text-3xl">
        O futuro do seu patrimônio, sob incerteza
      </h1>

      <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-content-body">
        O WealthLab simula milhares de trajetórias da sua carteira — com impostos, inflação e
        aportes do jeito brasileiro — e traduz tudo numa leitura clara: quanto você
        provavelmente terá, a chance de bater sua meta e o risco no caminho.
      </p>

      <div className="mx-auto mt-6 max-w-md rounded-lg border border-border bg-surface px-4 py-3">
        <p className="text-sm text-content-muted">
          Você está começando com uma <span className="text-content-body">carteira de exemplo</span>:
        </p>
        <div className="mt-2 flex flex-wrap justify-center gap-1.5">
          {holdings.map((h) => (
            <span
              key={h.asset.ticker}
              className="rounded bg-canvas px-2 py-0.5 text-xs text-content-body"
            >
              {h.asset.ticker}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <button
          onClick={onRunExample}
          className="inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
        >
          <Play size={16} aria-hidden="true" /> Rodar simulação de exemplo
        </button>
        <button
          onClick={onEditPortfolio}
          className="inline-flex items-center gap-2 rounded-lg border border-border px-5 py-2.5 text-sm font-semibold text-content-body transition-colors hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
        >
          <Pencil size={16} aria-hidden="true" /> Editar minha carteira
        </button>
      </div>

      <p className="mx-auto mt-6 max-w-md text-xs leading-relaxed text-content-subtle">
        Projeções estatísticas para fins de estudo — não são recomendação de investimento.
      </p>
    </section>
  )
}
