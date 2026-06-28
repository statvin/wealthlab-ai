import { lazy, Suspense, useEffect, useRef, useState, type ReactNode } from 'react'

import { api } from './api/client'
import type { HoldingDTO, Methodology } from './api/types'
import { ErrorState } from './components/ErrorState'
import { InsightsPanel } from './components/InsightsPanel'
import { MethodologyTab } from './components/MethodologyTab'
import { NavRail, type Aba } from './components/NavRail'
import { PortfolioEditor } from './components/PortfolioEditor'
import { RebalancePanel } from './components/RebalancePanel'
import { RetirementPanel } from './components/RetirementPanel'
import { ResultadoHero } from './components/ResultadoHero'
import { RiskPanel } from './components/RiskPanel'
import { MetodologiaSkeleton } from './components/Skeletons'
import { SimulationInputs } from './components/SimulationInputs'
import { StressPanel } from './components/StressPanel'
import { Skeleton } from './components/ui/Skeleton'
import { ThemeToggle } from './components/ui/ThemeToggle'
import { WelcomePanel } from './components/WelcomePanel'
import { INPUTS_PADRAO, useSimulation, type SimData, type SimInputs } from './hooks/useSimulation'
import { CARTEIRA_EXEMPLO } from './lib/defaultPortfolio'

// Gráficos carregados sob demanda: tiram o Plotly (~1,5MB) do bundle inicial, deixando
// o first paint leve. Cada um cai num chunk próprio, buscado só quando há resultados.
const MonteCarloFunnel = lazy(() =>
  import('./components/MonteCarloFunnel').then((m) => ({ default: m.MonteCarloFunnel })),
)
const FinalHistogram = lazy(() =>
  import('./components/FinalHistogram').then((m) => ({ default: m.FinalHistogram })),
)
const CorrelationHeatmap = lazy(() =>
  import('./components/CorrelationHeatmap').then((m) => ({ default: m.CorrelationHeatmap })),
)
import { montarTese } from './lib/narrative'

export default function App() {
  const [holdings, setHoldings] = useState<HoldingDTO[]>(CARTEIRA_EXEMPLO)
  const [inputs, setInputs] = useState<SimInputs>(INPUTS_PADRAO)
  const [aba, setAba] = useState<Aba>('dashboard')
  const [metodologia, setMetodologia] = useState<Methodology | null>(null)
  // Primeira visita: mostra boas-vindas em vez de já rodar a simulação de exemplo.
  const [mostrarBoasVindas, setMostrarBoasVindas] = useState(
    () => localStorage.getItem('wl-welcomed') !== '1',
  )
  const { loading, error, data, run } = useSimulation()

  // Carga da metodologia ao montar. A simulação inicial só roda se as boas-vindas já
  // foram dispensadas (do contrário, o usuário escolhe rodar pelo CTA do WelcomePanel).
  useEffect(() => {
    if (!mostrarBoasVindas) run(holdings, inputs)
    api.methodology().then(setMetodologia).catch(() => undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recálculo ao vivo: ao mexer nos parâmetros (sliders/avançados), re-roda com debounce
  // (~400ms). Pula a 1ª execução — a montagem acima já dispara o run inicial.
  const primeiraVez = useRef(true)
  useEffect(() => {
    if (primeiraVez.current) {
      primeiraVez.current = false
      return
    }
    if (mostrarBoasVindas) return
    const id = setTimeout(() => run(holdings, inputs), 400)
    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputs])

  function simular() {
    setAba('dashboard')
    run(holdings, inputs)
  }

  function dispensarBoasVindas() {
    localStorage.setItem('wl-welcomed', '1')
    setMostrarBoasVindas(false)
  }

  function rodarExemplo() {
    dispensarBoasVindas()
    setAba('dashboard')
    run(holdings, inputs)
  }

  function editarCarteiraDoWelcome() {
    dispensarBoasVindas()
    setAba('carteira')
  }

  return (
    <div className="flex min-h-screen bg-canvas">
      <NavRail aba={aba} onSelect={setAba} />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar aba={aba} />

        <main className="mx-auto w-full max-w-[1320px] flex-1 px-7 pb-10 pt-6">
          {aba === 'carteira' && (
            <div className="space-y-6">
              <PortfolioEditor holdings={holdings} onChange={setHoldings} />
              <button
                onClick={simular}
                disabled={loading || holdings.length === 0}
                className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50"
              >
                {loading ? 'Simulando…' : 'Salvar carteira e simular'}
              </button>
            </div>
          )}

          {aba === 'aposentadoria' && <RetirementPanel simId={data?.simId ?? null} />}

          {aba === 'metodologia' &&
            (metodologia ? (
              <MethodologyTab metodologia={metodologia} />
            ) : (
              <MetodologiaSkeleton />
            ))}

          {aba === 'dashboard' &&
            (mostrarBoasVindas ? (
              <WelcomePanel
                holdings={holdings}
                onRunExample={rodarExemplo}
                onEditPortfolio={editarCarteiraDoWelcome}
              />
            ) : (
              <Dashboard
                loading={loading}
                error={error}
                data={data}
                inputs={inputs}
                holdings={holdings}
                onChange={setInputs}
                onRun={simular}
                onEditCarteira={() => setAba('carteira')}
              />
            ))}
        </main>
      </div>
    </div>
  )
}

const ABA_LABEL: Record<Aba, string> = {
  dashboard: 'Dashboard',
  carteira: 'Carteira',
  aposentadoria: 'Aposentadoria',
  metodologia: 'Metodologia',
}

// Topbar Eclipse: marca + chip da aba à esquerda; selo "ao vivo" + tema + avatar à direita.
function Topbar({ aba }: { aba: Aba }) {
  return (
    <header className="flex items-center justify-between border-b border-hairline bg-chrome px-7 py-4">
      <div className="flex items-center gap-2.5">
        <span className="text-base tracking-tight">
          <span className="font-semibold text-content">WealthLab</span>{' '}
          <span className="font-normal text-content-muted">AI</span>
        </span>
        <span className="rounded-md border border-border px-2 py-[3px] text-[11px] text-content-muted">
          {ABA_LABEL[aba]}
        </span>
      </div>
      <div className="flex items-center gap-3.5">
        <span className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-border px-2.5 py-[5px] text-xs text-content-muted">
          <span
            className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand motion-safe:animate-[wlpulse_2.4s_ease-in-out_infinite]"
            style={{ boxShadow: '0 0 8px rgb(var(--brand))' }}
            aria-hidden="true"
          />
          Projeção ao vivo
        </span>
        <ThemeToggle />
        <div
          className="h-[30px] w-[30px] rounded-full border border-border bg-gradient-to-br from-surface-raised to-border"
          aria-hidden="true"
        />
      </div>
    </header>
  )
}

function Dashboard({
  loading,
  error,
  data,
  inputs,
  holdings,
  onChange,
  onRun,
  onEditCarteira,
}: {
  loading: boolean
  error: string | null
  data: SimData | null
  inputs: SimInputs
  holdings: HoldingDTO[]
  onChange: (i: SimInputs) => void
  onRun: () => void
  onEditCarteira: () => void
}) {
  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-[360px_1fr] lg:items-stretch">
        <SimulationInputs
          holdings={holdings}
          inputs={inputs}
          onChange={onChange}
          onRun={onRun}
          onEditCarteira={onEditCarteira}
          loading={loading}
        />

        {error ? (
          <ErrorState detalhe={error} onRetry={onRun} />
        ) : !data ? (
          <HeroSkeleton />
        ) : (
          <ResultadoHero
            resumo={data.resumo}
            risk={data.risk}
            tese={montarTese(data.resumo, data.results.funil, inputs.horizonteAnos, inputs.valorMeta)}
            horizonteAnos={inputs.horizonteAnos}
          />
        )}
      </div>

      {data && !error && <Resultados data={data} holdings={holdings} loading={loading} />}
    </div>
  )
}

function HeroSkeleton() {
  return (
    <div className="card-hero flex flex-col p-7 sm:p-[30px]" aria-hidden="true">
      <Skeleton className="h-3 w-48" />
      <Skeleton className="mt-4 h-12 w-2/5" />
      <Skeleton className="mt-4 h-5 w-3/4" />
      <Skeleton className="mt-6 h-2 w-full" />
      <div className="mt-auto grid grid-cols-3 gap-3 pt-6">
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
      </div>
    </div>
  )
}

function Resultados({
  data,
  holdings,
  loading,
}: {
  data: SimData
  holdings: HoldingDTO[]
  loading: boolean
}) {
  const { results, risk } = data

  return (
    <>
      {loading && (
        <div className="flex items-center gap-2 text-xs text-content-muted" aria-live="polite">
          <span
            className="h-1.5 w-1.5 rounded-full bg-brand motion-safe:animate-pulse"
            aria-hidden="true"
          />
          Atualizando projeção…
        </div>
      )}

      <InsightsPanel insights={data.insights} />

      <Secao titulo="Trajetória" sub="Como o patrimônio evolui ao longo do tempo e onde pode terminar">
        <div className="card">
          <h3 className="eyebrow mb-3">Projeção de Monte Carlo</h3>
          <Suspense fallback={<Skeleton className="h-80 w-full" />}>
            <MonteCarloFunnel funil={results.funil} />
          </Suspense>
        </div>
        <div className="card">
          <h3 className="eyebrow mb-3">Distribuição dos patrimônios finais</h3>
          <Suspense fallback={<Skeleton className="h-72 w-full" />}>
            <FinalHistogram histograma={results.histograma} />
          </Suspense>
        </div>
      </Secao>

      <Secao titulo="Risco" sub="Quanto pode cair e de onde vem o risco da carteira">
        <div className="grid gap-6 lg:grid-cols-2">
          <RiskPanel risk={risk} />
          <div className="card">
            <h3 className="eyebrow mb-3">Correlação (renda variável)</h3>
            <Suspense fallback={<Skeleton className="h-72 w-full" />}>
              <CorrelationHeatmap correlacao={results.correlacao} />
            </Suspense>
          </div>
        </div>
      </Secao>

      <Secao titulo="Cenários de stress" sub="Como a carteira se comporta em crises estilizadas — choques, não replays">
        <StressPanel simId={data.simId} />
      </Secao>

      <Secao titulo="Rebalanceamento" sub="Compras e vendas para voltar à alocação-alvo">
        <RebalancePanel simId={data.simId} holdings={holdings} />
      </Secao>
    </>
  )
}

function Secao({ titulo, sub, children }: { titulo: string; sub?: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-base font-semibold text-content">{titulo}</h2>
        {sub && <p className="mt-0.5 text-sm text-content-muted">{sub}</p>}
      </div>
      {children}
    </section>
  )
}
