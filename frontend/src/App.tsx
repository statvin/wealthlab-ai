import { useEffect, useState, type ReactNode } from 'react'

import { api } from './api/client'
import type { HoldingDTO, Methodology } from './api/types'
import { CorrelationHeatmap } from './components/CorrelationHeatmap'
import { FinalHistogram } from './components/FinalHistogram'
import { KpiCard } from './components/KpiCard'
import { MethodologyTab } from './components/MethodologyTab'
import { MonteCarloFunnel } from './components/MonteCarloFunnel'
import { PortfolioEditor } from './components/PortfolioEditor'
import { RiskPanel } from './components/RiskPanel'
import { Sidebar } from './components/Sidebar'
import { StressPanel } from './components/StressPanel'
import { INPUTS_PADRAO, useSimulation, type SimData, type SimInputs } from './hooks/useSimulation'
import { CARTEIRA_EXEMPLO } from './lib/defaultPortfolio'
import { fmtCompactBRL, fmtPct } from './lib/format'
import { pesosPorAtivo } from './lib/portfolio'

type Aba = 'dashboard' | 'carteira' | 'metodologia'

export default function App() {
  const [holdings, setHoldings] = useState<HoldingDTO[]>(CARTEIRA_EXEMPLO)
  const [inputs, setInputs] = useState<SimInputs>(INPUTS_PADRAO)
  const [aba, setAba] = useState<Aba>('dashboard')
  const [metodologia, setMetodologia] = useState<Methodology | null>(null)
  const { loading, error, data, run } = useSimulation()

  // Simulação inicial (sobre a carteira-exemplo) + carga da metodologia ao montar.
  useEffect(() => {
    run(holdings, inputs)
    api.methodology().then(setMetodologia).catch(() => undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function simular() {
    setAba('dashboard')
    run(holdings, inputs)
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-base-600/60 bg-base-800/50 px-4 py-3">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold text-accent">WealthLab</span>
            <span className="text-lg font-light text-slate-300">AI</span>
          </div>
          <nav className="flex gap-1 text-sm">
            <TabBtn ativo={aba === 'dashboard'} onClick={() => setAba('dashboard')}>
              Dashboard
            </TabBtn>
            <TabBtn ativo={aba === 'carteira'} onClick={() => setAba('carteira')}>
              Carteira
            </TabBtn>
            <TabBtn ativo={aba === 'metodologia'} onClick={() => setAba('metodologia')}>
              Metodologia
            </TabBtn>
          </nav>
        </div>
      </header>

      <main className="mx-auto flex max-w-7xl flex-col gap-4 p-4 lg:flex-row">
        {aba === 'dashboard' && (
          <Sidebar
            inputs={inputs}
            onChange={setInputs}
            onRun={simular}
            loading={loading}
          />
        )}

        <section className="min-w-0 flex-1 space-y-4">
          {aba === 'carteira' && (
            <>
              <PortfolioEditor holdings={holdings} onChange={setHoldings} />
              <button
                onClick={simular}
                disabled={loading || holdings.length === 0}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-base-900 hover:bg-accent-soft disabled:opacity-50"
              >
                {loading ? 'Simulando…' : 'Salvar carteira e simular'}
              </button>
            </>
          )}

          {aba === 'metodologia' &&
            (metodologia ? (
              <MethodologyTab metodologia={metodologia} />
            ) : (
              <Aviso texto="Carregando metodologia…" />
            ))}

          {aba === 'dashboard' && (
            <Dashboard loading={loading} error={error} data={data} holdings={holdings} />
          )}
        </section>
      </main>
    </div>
  )
}

function Dashboard({
  loading,
  error,
  data,
  holdings,
}: {
  loading: boolean
  error: string | null
  data: SimData | null
  holdings: HoldingDTO[]
}) {
  if (error) {
    return (
      <Aviso
        texto={`Erro ao rodar a simulação: ${error}. A API está no ar (uvicorn) e o cache de preços está populado?`}
        tom="erro"
      />
    )
  }
  if (!data) return <Aviso texto="Rodando simulação…" />

  const { resumo, results, risk } = data
  const vc95 = risk.var_cvar.find((v) => v.nivel === 0.95)
  const pesos = pesosPorAtivo(holdings)

  return (
    <>
      <div className="card flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
        <span className="label">Carteira simulada</span>
        {pesos.map(({ ticker, peso }) => (
          <span key={ticker} className="text-slate-300">
            {ticker} <span className="text-slate-500">{fmtPct(peso, 0)}</span>
          </span>
        ))}
        <span className="text-slate-500">· edite na aba “Carteira”</span>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard
          titulo="Patrimônio atual"
          valor={fmtCompactBRL(resumo.patrimonio_inicial)}
          tooltip="Valor inicial da carteira (soma das posições)."
        />
        <KpiCard
          titulo="Mediana (P50)"
          valor={fmtCompactBRL(resumo.nominal.p50)}
          destaque
          tooltip="Patrimônio nominal mediano ao fim do horizonte."
        />
        <KpiCard
          titulo="Otimista (P90)"
          valor={fmtCompactBRL(resumo.nominal.p90)}
          tooltip="90% dos cenários terminam abaixo deste valor."
        />
        <KpiCard
          titulo="Pessimista (P10)"
          valor={fmtCompactBRL(resumo.nominal.p10)}
          tooltip="Apenas 10% dos cenários terminam abaixo deste valor."
        />
        <KpiCard
          titulo="Prob. de meta"
          valor={resumo.prob_meta != null ? fmtPct(resumo.prob_meta) : '—'}
          tooltip="Fração de cenários com patrimônio ≥ meta no prazo definido."
        />
        <KpiCard
          titulo="Prob. de ruína"
          valor={fmtPct(resumo.prob_ruina)}
          tooltip="Fração de cenários que tocam zero antes do fim do horizonte."
        />
        <KpiCard
          titulo="VaR 95% (1 ano)"
          valor={fmtPct(vc95?.var ?? 0)}
          tooltip="Perda máxima esperada em 1 ano com 95% de confiança (risco de mercado)."
        />
        <KpiCard
          titulo="CVaR 95% (1 ano)"
          valor={fmtPct(vc95?.cvar ?? 0)}
          tooltip="Perda média nos 5% piores cenários de 1 ano (Expected Shortfall)."
        />
      </div>

      {loading && <p className="text-xs text-slate-500">Atualizando…</p>}

      <div className="card">
        <h3 className="mb-2 text-sm font-semibold text-slate-300">
          Projeção de Monte Carlo (nominal)
        </h3>
        <MonteCarloFunnel funil={results.funil} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-2 text-sm font-semibold text-slate-300">
            Correlação (renda variável)
          </h3>
          <CorrelationHeatmap correlacao={results.correlacao} />
        </div>
        <div className="card">
          <h3 className="mb-2 text-sm font-semibold text-slate-300">
            Distribuição dos patrimônios finais
          </h3>
          <FinalHistogram histograma={results.histograma} />
        </div>
      </div>

      <RiskPanel risk={risk} />
      <StressPanel simId={data.simId} />
    </>
  )
}

function TabBtn({
  ativo,
  onClick,
  children,
}: {
  ativo: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-lg px-3 py-1.5 transition ${
        ativo ? 'bg-accent text-base-900' : 'text-slate-300 hover:bg-base-700'
      }`}
    >
      {children}
    </button>
  )
}

function Aviso({ texto, tom = 'info' }: { texto: string; tom?: 'info' | 'erro' }) {
  return (
    <div
      className={`card text-sm ${tom === 'erro' ? 'text-rose-300' : 'text-slate-400'}`}
    >
      {texto}
    </div>
  )
}
