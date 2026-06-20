import { useEffect, useState } from 'react'
import { Menu, SlidersHorizontal, X } from 'lucide-react'

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
import { RiskPanel } from './components/RiskPanel'
import { Sidebar } from './components/Sidebar'
import { StressPanel } from './components/StressPanel'
import { Badge, type BadgeTone } from './components/ui/Badge'
import { Stat } from './components/ui/Stat'
import { INPUTS_PADRAO, useSimulation, type SimData, type SimInputs } from './hooks/useSimulation'
import { CARTEIRA_EXEMPLO } from './lib/defaultPortfolio'
import { fmtCompactBRL, fmtPct } from './lib/format'
import { montarTese, type NivelRuina } from './lib/narrative'
import { valorTotal } from './lib/portfolio'

const TITULOS: Record<Aba, string> = {
  dashboard: 'Dashboard',
  carteira: 'Carteira',
  aposentadoria: 'Aposentadoria',
  metodologia: 'Metodologia',
}

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
  const [navOpen, setNavOpen] = useState(false)
  const [paramsOpen, setParamsOpen] = useState(false)
  const { loading, error, data, run } = useSimulation()

  // Simulação inicial (sobre a carteira-exemplo) + carga da metodologia ao montar.
  useEffect(() => {
    run(holdings, inputs)
    api.methodology().then(setMetodologia).catch(() => undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Fecha os overlays com Esc.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setNavOpen(false)
        setParamsOpen(false)
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  function simular() {
    setParamsOpen(false)
    setAba('dashboard')
    run(holdings, inputs)
  }

  return (
    <div className="flex min-h-screen">
      <NavRail aba={aba} onSelect={setAba} open={navOpen} onClose={() => setNavOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          titulo={TITULOS[aba]}
          holdings={holdings}
          aba={aba}
          loading={loading}
          onMenu={() => setNavOpen(true)}
          onParametros={() => setParamsOpen(true)}
          onRun={simular}
        />

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
            <Dashboard loading={loading} error={error} data={data} inputs={inputs} holdings={holdings} />
          )}
        </main>
      </div>

      {/* Painel de parâmetros (slide-over à direita; funciona no mobile). */}
      {paramsOpen && (
        <div
          className="fixed inset-0 z-40"
          role="dialog"
          aria-modal="true"
          aria-label="Parâmetros da simulação"
        >
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setParamsOpen(false)}
            aria-hidden="true"
          />
          <aside className="absolute right-0 top-0 flex h-full w-80 max-w-[90vw] flex-col overflow-auto border-l border-border bg-surface p-4 shadow-xl">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-content">Parâmetros</h2>
              <button
                onClick={() => setParamsOpen(false)}
                aria-label="Fechar parâmetros"
                className="rounded p-1 text-content-muted transition-colors hover:text-content focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
              >
                <X size={18} />
              </button>
            </div>
            <Sidebar inputs={inputs} onChange={setInputs} onRun={simular} loading={loading} />
          </aside>
        </div>
      )}
    </div>
  )
}

function TopBar({
  titulo,
  holdings,
  aba,
  loading,
  onMenu,
  onParametros,
  onRun,
}: {
  titulo: string
  holdings: HoldingDTO[]
  aba: Aba
  loading: boolean
  onMenu: () => void
  onParametros: () => void
  onRun: () => void
}) {
  const total = valorTotal(holdings)
  const n = holdings.length
  const carteira = `Carteira · ${fmtCompactBRL(total)} · ${n} ${n === 1 ? 'ativo' : 'ativos'}`

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-canvas/80 px-4 py-3 backdrop-blur sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          onClick={onMenu}
          aria-label="Abrir navegação"
          className="rounded-lg p-1.5 text-content-muted transition-colors hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 lg:hidden"
        >
          <Menu size={20} />
        </button>
        {/* Mobile: título da seção (o rail está oculto). Desktop: contexto da carteira. */}
        <h1 className="truncate text-base font-semibold text-content lg:hidden">{titulo}</h1>
        <span className="hidden truncate text-sm text-content-muted lg:inline">{carteira}</span>
      </div>

      {aba === 'dashboard' && (
        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <button
            onClick={onParametros}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm text-content-body transition-colors hover:bg-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
          >
            <SlidersHorizontal size={16} />
            <span className="hidden sm:inline">Parâmetros</span>
          </button>
          <button
            onClick={onRun}
            disabled={loading}
            className="rounded-lg bg-brand px-3 py-1.5 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50"
          >
            {loading ? 'Rodando…' : 'Rodar simulação'}
          </button>
        </div>
      )}
    </header>
  )
}

function Dashboard({
  loading,
  error,
  data,
  inputs,
  holdings,
}: {
  loading: boolean
  error: string | null
  data: SimData | null
  inputs: SimInputs
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
  const tese = montarTese(resumo, results.funil, inputs.horizonteAnos, inputs.valorMeta)

  return (
    <div className="space-y-6">
      {/* HERÓI — bloco único: número provável + frase-tese + números de apoio. */}
      <section className="card-hero">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <Stat
            size="hero"
            label={`Patrimônio provável em ${Math.round(inputs.horizonteAnos)} anos`}
            value={fmtCompactBRL(resumo.nominal.p50)}
            sub={
              <>
                Hoje {fmtCompactBRL(resumo.patrimonio_inicial)} ·{' '}
                <span className="text-gain">
                  +{fmtCompactBRL(resumo.nominal.p50 - resumo.patrimonio_inicial)} projetado
                </span>
              </>
            }
          />
          <div className="lg:max-w-md">
            <p className="text-lg leading-relaxed text-content sm:text-xl">{tese.frase}</p>
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

        <div className="mt-6 grid grid-cols-2 gap-4 border-t border-border pt-5 sm:grid-cols-4">
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
      </section>

      {loading && <p className="text-xs text-content-subtle">Atualizando…</p>}

      {/* MIOLO — coluna principal (gráficos) + coluna lateral (insights, risco). */}
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

      {/* FERRAMENTAS — seções de largura cheia. */}
      <StressPanel simId={data.simId} />
      <RebalancePanel simId={data.simId} holdings={holdings} />
    </div>
  )
}

function Aviso({ texto, tom = 'info' }: { texto: string; tom?: 'info' | 'erro' }) {
  return (
    <div className={`card text-sm ${tom === 'erro' ? 'text-loss' : 'text-content-muted'}`}>
      {texto}
    </div>
  )
}
