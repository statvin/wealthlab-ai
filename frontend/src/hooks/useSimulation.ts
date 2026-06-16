// Hook que orquestra o fluxo de simulação SEM bibliotecas de estado:
//   1) cria a carteira-modelo (uma vez, guardada num ref)
//   2) roda a simulação com os parâmetros da sidebar
//   3) busca resultados + análise de risco em paralelo
// Expõe { loading, error, data, run } — estados explícitos, fáceis de seguir.

import { useCallback, useRef, useState } from 'react'

import { api } from '../api/client'
import type {
  HoldingDTO,
  Insight,
  RebalanceMode,
  Resumo,
  ResultsOut,
  RiskAnalysisOut,
  SimulationRunRequest,
} from '../api/types'
import { targetFromHoldings } from '../lib/portfolio'

export interface SimInputs {
  horizonteAnos: number
  aporteMensal: number
  saqueMensal: number
  inflacaoAa: number
  valorMeta: number
  prazoMetaAnos: number
  nCenarios: number
  rebalanceamento: RebalanceMode
  df: number
  seed: number
}

export const INPUTS_PADRAO: SimInputs = {
  horizonteAnos: 30,
  aporteMensal: 2000,
  saqueMensal: 0,
  inflacaoAa: 0.04,
  valorMeta: 3_000_000,
  prazoMetaAnos: 30,
  nCenarios: 10_000,
  rebalanceamento: 'ANUAL_AO_ALVO',
  df: 6,
  seed: 42,
}

export interface SimData {
  simId: number
  resumo: Resumo
  results: ResultsOut
  risk: RiskAnalysisOut
  insights: Insight[]
}

export function useSimulation() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<SimData | null>(null)
  const portfolioId = useRef<number | null>(null)

  const holdingsKey = useRef<string>('')

  const run = useCallback(async (holdings: HoldingDTO[], inputs: SimInputs) => {
    if (holdings.length === 0) {
      setError('Adicione ao menos um ativo à carteira (aba Carteira).')
      return
    }
    setLoading(true)
    setError(null)
    try {
      // (Re)cria a carteira no backend só quando a composição muda.
      const key = JSON.stringify(holdings)
      if (key !== holdingsKey.current || portfolioId.current == null) {
        const pf = await api.criarPortfolio({ nome: 'Minha carteira', holdings })
        portfolioId.current = pf.id
        holdingsKey.current = key
      }
      const pid = portfolioId.current! // garantidamente definido aqui

      const req: SimulationRunRequest = {
        portfolio_id: pid,
        config: {
          n_cenarios: inputs.nCenarios,
          horizonte_anos: inputs.horizonteAnos,
          seed: inputs.seed,
          inflacao_aa: inputs.inflacaoAa,
          rebalanceamento: inputs.rebalanceamento,
          df_tstudent: inputs.df,
        },
        premissas_juros: { selic_aa: 0.105, ipca_aa: inputs.inflacaoAa },
        cashflow: { aporte_mensal: inputs.aporteMensal, saque_mensal: inputs.saqueMensal },
        target: inputs.rebalanceamento === 'ANUAL_AO_ALVO' ? targetFromHoldings(holdings) : null,
        goal: { valor_meta: inputs.valorMeta, prazo_anos: inputs.prazoMetaAnos },
      }

      const runRes = await api.rodarSimulacao(req)
      const [results, risk, insightsRes] = await Promise.all([
        api.resultados(runRes.id),
        api.riskAnalysis(runRes.id),
        api.insights(runRes.id),
      ])
      setData({
        simId: runRes.id,
        resumo: runRes.resumo,
        results,
        risk,
        insights: insightsRes.insights,
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  return { loading, error, data, run }
}
