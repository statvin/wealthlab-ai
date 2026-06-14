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
      <h3 className="mb-3 text-sm font-semibold text-slate-300">{titulo}</h3>
      <dl className="space-y-3">
        {Object.entries(itens).map(([chave, texto]) => (
          <div key={chave}>
            <dt className="text-sm font-medium text-accent">{rotulos[chave] ?? chave}</dt>
            <dd className="text-sm text-slate-300">{texto}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export function MethodologyTab({ metodologia }: { metodologia: Methodology }) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-200">
        <strong>Aviso.</strong> {metodologia.aviso}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Secao titulo="Premissas" itens={metodologia.premissas} rotulos={TITULOS_PREMISSAS} />
        <Secao titulo="Métricas" itens={metodologia.metricas} rotulos={TITULOS_METRICAS} />
      </div>
      <div className="card">
        <h3 className="mb-2 text-sm font-semibold text-slate-300">Stress testing</h3>
        <p className="text-sm text-slate-300">{metodologia.stress}</p>
      </div>
    </div>
  )
}
