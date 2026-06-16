import { useCallback, useState } from 'react'

import { api } from '../api/client'
import type { RebalanceOut, TargetAllocationDTO } from '../api/types'

export function useRebalance(simId: number | null) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<RebalanceOut | null>(null)

  const run = useCallback(
    async (target: TargetAllocationDTO) => {
      if (simId == null) return
      setLoading(true)
      setError(null)
      try {
        setData(await api.rebalance(simId, target))
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
