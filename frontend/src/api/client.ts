// Wrapper fetch tipado à mão. Um único `req<T>` centraliza a chamada, o header
// JSON e o tratamento de erro; os métodos abaixo só dizem o tipo de retorno.

import type {
  InsightsOut,
  Methodology,
  PortfolioCreate,
  PortfolioOut,
  RebalanceOut,
  ResultsOut,
  RetirementOut,
  RetirementRequest,
  RiskAnalysisOut,
  SimulationRunRequest,
  SimulationRunResponse,
  StressOut,
  TargetAllocationDTO,
} from './types'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail: unknown
    try {
      detail = (await res.json()).detail
    } catch {
      detail = res.statusText
    }
    const msg = typeof detail === 'string' ? detail : JSON.stringify(detail)
    throw new ApiError(res.status, msg)
  }
  return (await res.json()) as T
}

export const api = {
  criarPortfolio: (body: PortfolioCreate) =>
    req<PortfolioOut>('/portfolio', { method: 'POST', body: JSON.stringify(body) }),

  rodarSimulacao: (body: SimulationRunRequest) =>
    req<SimulationRunResponse>('/simulation/run', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  resultados: (id: number) => req<ResultsOut>(`/simulation/${id}/results`),

  riskAnalysis: (id: number) => req<RiskAnalysisOut>(`/simulation/${id}/risk-analysis`),

  stressTest: (id: number, presets?: string[]) =>
    req<StressOut>(
      `/simulation/${id}/stress-test` +
        (presets && presets.length ? `?presets=${presets.join(',')}` : ''),
    ),

  methodology: () => req<Methodology>('/methodology'),

  insights: (id: number) => req<InsightsOut>(`/simulation/${id}/insights`),

  rebalance: (id: number, target: TargetAllocationDTO) =>
    req<RebalanceOut>(`/simulation/${id}/rebalance`, {
      method: 'POST',
      body: JSON.stringify(target),
    }),

  retirement: (id: number, body: RetirementRequest) =>
    req<RetirementOut>(`/simulation/${id}/retirement`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
