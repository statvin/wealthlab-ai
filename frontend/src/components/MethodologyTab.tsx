// Aba Metodologia — expõe as premissas vindas de GET /methodology.

import type { Methodology } from '../api/types'

const TITULOS_PREMISSAS: Record<string, string> = {
  renda_variavel: 'Renda variável',
  cripto: 'Cripto',
  renda_fixa: 'Renda fixa',
  correlacao: 'Correlação',
  tributacao: 'Tributação',
  inflacao: 'Inflação',
}

const TITULOS_METRICAS: Record<string, string> = {
  var_cvar: 'VaR / CVaR',
  prob_ruina: 'Probabilidade de ruína',
  prob_meta: 'Probabilidade de meta',
  drawdown: 'Drawdown',
  contribuicao_risco: 'Contribuição ao risco',
}

function Secao({ titulo, itens, rotulos }: {
  titulo: string
  itens: Record<string, string>
  rotulos: Record<string, string>
}) {
  return (
    <div className="card">
      <h3 className="mb-3 text-sm font-semibold text-content-body">{titulo}</h3>
      <dl className="space-y-3">
        {Object.entries(itens).map(([chave, texto]) => (
          <div key={chave}>
            <dt className="text-sm font-medium text-brand">{rotulos[chave] ?? chave}</dt>
            <dd className="text-sm text-content-body">{texto}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export function MethodologyTab({ metodologia }: { metodologia: Methodology }) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-warning/40 bg-warning/10 p-4 text-sm text-warning">
        <strong>Aviso.</strong> {metodologia.aviso}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Secao titulo="Premissas" itens={metodologia.premissas} rotulos={TITULOS_PREMISSAS} />
        <Secao titulo="Métricas" itens={metodologia.metricas} rotulos={TITULOS_METRICAS} />
      </div>
      <div className="card">
        <h3 className="mb-2 text-sm font-semibold text-content-body">Stress testing</h3>
        <p className="text-sm text-content-body">{metodologia.stress}</p>
      </div>
    </div>
  )
}
