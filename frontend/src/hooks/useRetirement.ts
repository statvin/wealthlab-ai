import { useCallback, useState } from 'react'

import { api } from '../api/client'
import type { RetirementOut, RetirementRequest } from '../api/types'

export function useRetirement(simId: number | null) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<RetirementOut | null>(null)

  const run = useCallback(
    async (req: RetirementRequest) => {
      if (simId == null) return
      setLoading(true)
      setError(null)
      try {
        setData(await api.retirement(simId, req))
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
