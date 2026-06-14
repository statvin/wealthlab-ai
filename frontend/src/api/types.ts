// Tipos TypeScript que ESPELHAM os DTOs do backend (wealthlab_api/schemas.py).
// Mantidos à mão: ao mudar um DTO no backend, atualize aqui também. É o custo
// consciente do "wrapper à mão" — em troca, zero tooling de geração.

export type AssetClass =
  | 'EQUITY_BR'
  | 'EQUITY_INTL'
  | 'CRYPTO'
  | 'FIXED_INCOME_POS'
  | 'FIXED_INCOME_IPCA'

export type Indexador = 'CDI' | 'SELIC' | 'IPCA' | 'PREFIXADO'
export type RebalanceMode = 'NENHUM' | 'ANUAL_AO_ALVO'

export interface FixedIncomeTerms {
  indexador: Indexador
  taxa_contratada: number
  duration_anos?: number
  vencimento?: string | null
}

export interface AssetDTO {
  ticker: string
  nome: string
  classe: AssetClass
  fixed_income_terms?: FixedIncomeTerms | null
}

export interface HoldingDTO {
  asset: AssetDTO
  quantidade: number
  preco_inicial?: number
}

export interface PortfolioCreate {
  nome?: string
  holdings: HoldingDTO[]
}

export interface PortfolioOut {
  id: number
  nome: string
  holdings: {
    ticker: string
    nome: string
    classe: AssetClass
    quantidade: number
    preco_inicial: number
  }[]
}

// ----------------------------- entrada de simulação -----------------------
export interface SimulationConfigDTO {
  n_cenarios?: number
  horizonte_anos?: number
  seed?: number
  inflacao_aa?: number
  rebalanceamento?: RebalanceMode
  df_tstudent?: number
}

export interface PremissasJurosDTO {
  selic_aa?: number
  ipca_aa?: number
}

export interface CashFlowDTO {
  aporte_mensal?: number
  saque_mensal?: number
  inicio_mes?: number
  fim_mes?: number | null
  corrigir_por_inflacao?: boolean
}

export interface TargetAllocationDTO {
  por_classe: Partial<Record<AssetClass, number>>
}

export interface GoalDTO {
  valor_meta: number
  prazo_anos: number
}

export interface SimulationRunRequest {
  portfolio_id: number
  config?: SimulationConfigDTO
  premissas_juros?: PremissasJurosDTO
  cashflow?: CashFlowDTO | null
  target?: TargetAllocationDTO | null
  goal?: GoalDTO | null
}

// ----------------------------- saída de simulação -------------------------
export interface Percentis {
  p10: number
  p50: number
  p90: number
}

export interface Resumo {
  patrimonio_inicial: number
  nominal: Percentis
  real: Percentis
  prob_ruina: number
  prob_meta: number | null
}

export interface SimulationRunResponse {
  id: number
  status: string
  resumo: Resumo
}

export interface Funil {
  meses: number[]
  amostra: number[][] // ~100 trajetórias
  bandas: Record<string, number[]> // p5, p10, p50, p90, p95
}

export interface Histograma {
  edges: number[]
  counts: number[]
}

export interface Correlacao {
  labels: string[]
  matriz: number[][]
}

export interface ResultsOut {
  id: number
  resumo: Resumo
  funil: Funil
  histograma: Histograma
  correlacao: Correlacao
}

export interface VaRCVaR {
  nivel: number
  var: number
  cvar: number
}

export interface Drawdown {
  medio: number
  mediano: number
  pior: number
}

export interface Contribuicao {
  ordem: string[]
  pctr: number[]
  contrib_vol: number[]
  vol_anual_carteira: number
  por_classe: Record<string, number>
}

export interface RiskAnalysisOut {
  id: number
  var_cvar: VaRCVaR[]
  prob_ruina: number
  prob_meta: number | null
  drawdown: Drawdown
  contribuicao: Contribuicao
}

export interface StressComparacao {
  nome: string
  descricao: string
  resumo: Record<string, [number, number]> // métrica -> [base, stress]
}

export interface StressOut {
  id: number
  comparacoes: StressComparacao[]
}

export interface Methodology {
  aviso: string
  premissas: Record<string, string>
  metricas: Record<string, string>
  stress: string
}
