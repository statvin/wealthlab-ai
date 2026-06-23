import { lazy, Suspense, useEffect, useState, type ReactNode } from 'react'
import { Menu } from 'lucide-react'

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
import { MetodologiaSkeleton, ResultadosSkeleton } from './components/Skeletons'
import { SimulationInputs } from './components/SimulationInputs'
import { StressPanel } from './components/StressPanel'
import { Skeleton } from './components/ui/Skeleton'
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
  const [navOpen, setNavOpen] = useState(false)
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

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setNavOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

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
    <div className="flex min-h-screen">
      <NavRail aba={aba} onSelect={setAba} open={navOpen} onClose={() => setNavOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar onMenu={() => setNavOpen(true)} />

        <main className="mx-auto w-full max-w-6xl flex-1 p-4 sm:p-6">
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

// Barra mínima só no mobile (o rail está oculto): menu + marca.
function TopBar({ onMenu }: { onMenu: () => void }) {
  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-border bg-canvas/80 px-4 py-3 backdrop-blur lg:hidden">
      <button
        onClick={onMenu}
        aria-label="Abrir navegação"
        className="rounded-lg p-1.5 text-content-muted transition-colors hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
      >
        <Menu size={20} />
      </button>
      <span className="text-base">
        <span className="font-semibold text-brand">WealthLab</span>{' '}
        <span className="font-light text-content-muted">AI</span>
      </span>
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
    <div className="space-y-6">
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
        <ResultadosSkeleton />
      ) : (
        <Resultados data={data} inputs={inputs} holdings={holdings} loading={loading} />
      )}
    </div>
  )
}

function Resultados({
  data,
  inputs,
  holdings,
  loading,
}: {
  data: SimData
  inputs: SimInputs
  holdings: HoldingDTO[]
  loading: boolean
}) {
  const { resumo, results, risk } = data
  const tese = montarTese(resumo, results.funil, inputs.horizonteAnos, inputs.valorMeta)

  return (
    <>
      <ResultadoHero resumo={resumo} risk={risk} tese={tese} />

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
