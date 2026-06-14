// Busca a comparação Base vs. Stress de um preset, sob demanda (botão).

import { useCallback, useState } from 'react'

import { api } from '../api/client'
import type { StressComparacao } from '../api/types'

export function useStress(simId: number | null) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<StressComparacao | null>(null)

  const run = useCallback(
    async (preset: string) => {
      if (simId == null) return
      setLoading(true)
      setError(null)
      try {
        const res = await api.stressTest(simId, [preset])
        setData(res.comparacoes[0] ?? null)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    },
    [simId],
  )

  return { loading, error, data, run }
}
