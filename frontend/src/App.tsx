import { useEffect, useState } from 'react'
import { Menu } from 'lucide-react'

import { api } from './api/client'
import type { HoldingDTO, Methodology } from './api/types'
import { CorrelationHeatmap } from './components/CorrelationHeatmap'
import { FinalHistogram } from './components/FinalHistogram'
import { InsightsPanel } from './components/InsightsPanel'
import { MethodologyTab } from './components/MethodologyTab'
import { MonteCarloFunnel } from './components/MonteCarloFunnel'
import { NavRail, type Aba } from './components/NavRail'
import { PortfolioEditor } from './components/PortfolioEditor'
import { RebalancePanel } from './components/RebalancePanel'
import { RetirementPanel } from './components/RetirementPanel'
import { ResultadoHero } from './components/ResultadoHero'
import { RiskPanel } from './components/RiskPanel'
import { SimulationInputs } from './components/SimulationInputs'
import { StressPanel } from './components/StressPanel'
import { INPUTS_PADRAO, useSimulation, type SimData, type SimInputs } from './hooks/useSimulation'
import { CARTEIRA_EXEMPLO } from './lib/defaultPortfolio'
import { montarTese } from './lib/narrative'

const TITULOS: Record<Aba, string> = {
  dashboard: 'Dashboard',
  carteira: 'Carteira',
  aposentadoria: 'Aposentadoria',
  metodologia: 'Metodologia',
}

export default function App() {
  const [holdings, setHoldings] = useState<HoldingDTO[]>(CARTEIRA_EXEMPLO)
  const [inputs, setInputs] = useState<SimInputs>(INPUTS_PADRAO)
  const [aba, setAba] = useState<Aba>('dashboard')
  const [metodologia, setMetodologia] = useState<Methodology | null>(null)
  const [navOpen, setNavOpen] = useState(false)
  const { loading, error, data, run } = useSimulation()

  // Simulação inicial (sobre a carteira-exemplo) + carga da metodologia ao montar.
  useEffect(() => {
    run(holdings, inputs)
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

  return (
    <div className="flex min-h-screen">
      <NavRail aba={aba} onSelect={setAba} open={navOpen} onClose={() => setNavOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar titulo={TITULOS[aba]} onMenu={() => setNavOpen(true)} />

        <main className="mx-auto w-full max-w-6xl flex-1 p-4 sm:p-6">
          {aba === 'carteira' && (
            <div className="space-y-6">
              <PortfolioEditor holdings={holdings} onChange={setHoldings} />
              <button
                onClick={simular}
                disabled={loading || holdings.length === 0}
                className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong disabled:opacity-50"
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
              <Aviso texto="Carregando metodologia…" />
            ))}

          {aba === 'dashboard' && (
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
          )}
        </main>
      </div>
    </div>
  )
}

function TopBar({ titulo, onMenu }: { titulo: string; onMenu: () => void }) {
  return (
    <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-border bg-canvas/80 px-4 py-3 backdrop-blur sm:px-6">
      <button
        onClick={onMenu}
        aria-label="Abrir navegação"
        className="rounded-lg p-1.5 text-content-muted transition-colors hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 lg:hidden"
      >
        <Menu size={20} />
      </button>
      <h1 className="text-base font-semibold text-content">{titulo}</h1>
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
        <Aviso
          texto={`Erro ao rodar a simulação: ${error}. A API está no ar (uvicorn) e o cache de preços está populado?`}
          tom="erro"
        />
      ) : !data ? (
        <Aviso texto="Rodando simulação…" />
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

      {loading && <p className="text-xs text-content-subtle">Atualizando…</p>}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="card">
            <h2 className="eyebrow mb-3">Projeção de Monte Carlo</h2>
            <MonteCarloFunnel funil={results.funil} />
          </section>
          <div className="grid gap-6 sm:grid-cols-2">
            <section className="card">
              <h2 className="eyebrow mb-3">Distribuição dos finais</h2>
              <FinalHistogram histograma={results.histograma} />
            </section>
            <section className="card">
              <h2 className="eyebrow mb-3">Correlação (renda variável)</h2>
              <CorrelationHeatmap correlacao={results.correlacao} />
            </section>
          </div>
        </div>

        <div className="space-y-6">
          <InsightsPanel insights={data.insights} />
          <RiskPanel risk={risk} />
        </div>
      </div>

      <StressPanel simId={data.simId} />
      <RebalancePanel simId={data.simId} holdings={holdings} />
    </>
  )
}

function Aviso({ texto, tom = 'info' }: { texto: string; tom?: 'info' | 'erro' }) {
  return (
    <div className={`card text-sm ${tom === 'erro' ? 'text-loss' : 'text-content-muted'}`}>
      {texto}
    </div>
  )
}
