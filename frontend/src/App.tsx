import { useEffect, useState, type ReactNode } from 'react'

import { api } from './api/client'
import type { HoldingDTO, Methodology } from './api/types'
import { CorrelationHeatmap } from './components/CorrelationHeatmap'
import { FinalHistogram } from './components/FinalHistogram'
import { InsightsPanel } from './components/InsightsPanel'
import { MethodologyTab } from './components/MethodologyTab'
import { MonteCarloFunnel } from './components/MonteCarloFunnel'
import { PortfolioEditor } from './components/PortfolioEditor'
import { RebalancePanel } from './components/RebalancePanel'
import { RetirementPanel } from './components/RetirementPanel'
import { RiskPanel } from './components/RiskPanel'
import { Sidebar } from './components/Sidebar'
import { StressPanel } from './components/StressPanel'
import { Badge, type BadgeTone } from './components/ui/Badge'
import { Stat } from './components/ui/Stat'
import { INPUTS_PADRAO, useSimulation, type SimData, type SimInputs } from './hooks/useSimulation'
import { CARTEIRA_EXEMPLO } from './lib/defaultPortfolio'
import { fmtCompactBRL, fmtPct } from './lib/format'
import { montarTese, type NivelRuina } from './lib/narrative'
import { pesosPorAtivo } from './lib/portfolio'

type Aba = 'dashboard' | 'carteira' | 'aposentadoria' | 'metodologia'

const RUINA_TONE: Record<NivelRuina, BadgeTone> = {
  baixo: 'success',
  moderado: 'warning',
  alto: 'danger',
}

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
      <header className="border-b border-ink-700/60 bg-ink-850/50 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-semibold text-accent">WealthLab</span>
            <span className="text-lg font-light text-slate-400">AI</span>
          </div>
          <nav className="flex gap-1 text-sm">
            <TabBtn ativo={aba === 'dashboard'} onClick={() => setAba('dashboard')}>
              Dashboard
            </TabBtn>
            <TabBtn ativo={aba === 'carteira'} onClick={() => setAba('carteira')}>
              Carteira
            </TabBtn>
            <TabBtn ativo={aba === 'aposentadoria'} onClick={() => setAba('aposentadoria')}>
              Aposentadoria
            </TabBtn>
            <TabBtn ativo={aba === 'metodologia'} onClick={() => setAba('metodologia')}>
              Metodologia
            </TabBtn>
          </nav>
        </div>
      </header>

      <main className="mx-auto flex max-w-7xl flex-col gap-6 p-4 sm:p-6 lg:flex-row">
        {aba === 'dashboard' && (
          <Sidebar inputs={inputs} onChange={setInputs} onRun={simular} loading={loading} />
        )}

        <section className="min-w-0 flex-1 space-y-6">
          {aba === 'carteira' && (
            <>
              <PortfolioEditor holdings={holdings} onChange={setHoldings} />
              <button
                onClick={simular}
                disabled={loading || holdings.length === 0}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-ink-950 transition-colors hover:bg-accent-soft disabled:opacity-50"
              >
                {loading ? 'Simulando…' : 'Salvar carteira e simular'}
              </button>
            </>
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
              holdings={holdings}
              inputs={inputs}
            />
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
  inputs,
}: {
  loading: boolean
  error: string | null
  data: SimData | null
  holdings: HoldingDTO[]
  inputs: SimInputs
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
  const tese = montarTese(resumo, results.funil, inputs.horizonteAnos, inputs.valorMeta)

  return (
    <>
      {/* Hero — número provável + frase-tese (elemento-assinatura). */}
      <div className="card-hero">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <Stat
            size="hero"
            tone="accent"
            label={`Patrimônio provável em ${Math.round(inputs.horizonteAnos)} anos`}
            value={fmtCompactBRL(resumo.nominal.p50)}
            sub={`Hoje: ${fmtCompactBRL(resumo.patrimonio_inicial)}`}
          />
          <div className="lg:max-w-md">
            <p className="text-lg leading-relaxed text-slate-100 sm:text-xl">{tese.frase}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge>
                Faixa {fmtCompactBRL(tese.faixaP10)}–{fmtCompactBRL(tese.faixaP90)}
              </Badge>
              {tese.metaAtingivelAnos != null && (
                <Badge tone="success">Meta atingível em {tese.metaAtingivelAnos} anos</Badge>
              )}
              <Badge tone={RUINA_TONE[tese.nivelRuina]}>Risco de ruína {tese.nivelRuina}</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Carteira simulada — contexto sutil. */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className="eyebrow">Carteira simulada</span>
        {pesos.map(({ ticker, peso }) => (
          <span key={ticker} className="text-slate-300">
            {ticker} <span className="text-slate-500">{fmtPct(peso, 0)}</span>
          </span>
        ))}
        <span className="text-slate-500">· edite na aba “Carteira”</span>
      </div>

      <InsightsPanel insights={data.insights} />

      {/* KPIs secundários (menores, abaixo do herói). */}
      <div className="card grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat
          size="sm"
          label="Otimista (P90)"
          value={fmtCompactBRL(resumo.nominal.p90)}
          tooltip="90% dos cenários terminam abaixo deste valor."
        />
        <Stat
          size="sm"
          label="Pessimista (P10)"
          value={fmtCompactBRL(resumo.nominal.p10)}
          tooltip="Apenas 10% dos cenários terminam abaixo deste valor."
        />
        <Stat
          size="sm"
          label="VaR 95% (1 ano)"
          value={fmtPct(vc95?.var ?? 0)}
          tooltip="Perda máxima esperada em 1 ano com 95% de confiança (risco de mercado)."
        />
        <Stat
          size="sm"
          label="Vol. anual"
          value={fmtPct(risk.contribuicao.vol_anual_carteira)}
          tooltip="Volatilidade anualizada da carteira (a renda variável domina)."
        />
      </div>

      {loading && <p className="text-xs text-slate-500">Atualizando…</p>}

      <div className="card">
        <h3 className="eyebrow mb-3">Projeção de Monte Carlo (nominal)</h3>
        <MonteCarloFunnel funil={results.funil} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="eyebrow mb-3">Correlação (renda variável)</h3>
          <CorrelationHeatmap correlacao={results.correlacao} />
        </div>
        <div className="card">
          <h3 className="eyebrow mb-3">Distribuição dos patrimônios finais</h3>
          <FinalHistogram histograma={results.histograma} />
        </div>
      </div>

      <RiskPanel risk={risk} />
      <StressPanel simId={data.simId} />
      <RebalancePanel simId={data.simId} holdings={holdings} />
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
      className={`rounded-lg px-3 py-1.5 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 ${
        ativo ? 'bg-accent text-ink-950' : 'text-slate-300 hover:bg-ink-700'
      }`}
    >
      {children}
    </button>
  )
}

function Aviso({ texto, tom = 'info' }: { texto: string; tom?: 'info' | 'erro' }) {
  return (
    <div className={`card text-sm ${tom === 'erro' ? 'text-semantic-danger' : 'text-slate-400'}`}>
      {texto}
    </div>
  )
}
