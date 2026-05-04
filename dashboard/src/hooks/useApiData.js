/**
 * useApiData — fetches live theme + sentiment data from the NSE pipeline backend.
 * Re-fetches whenever filters change.  Returns null data when the API is offline.
 */
import { useState, useEffect, useCallback } from 'react'
import { fetchThemes, fetchSentiment, fetchCompare, checkHealth } from '../services/api'

export function useApiData(filters) {
  const [themes,    setThemes]    = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [compare,   setCompare]   = useState(null)
  const [isLive,    setIsLive]    = useState(false)
  const [loading,   setLoading]   = useState(true)

  // Stable serialised key so useCallback only fires when filters actually change
  const filterKey = JSON.stringify(filters)

  const refresh = useCallback(async () => {
    setLoading(true)
    const [healthy, themeData, sentimentData, compareData] = await Promise.all([
      checkHealth(),
      fetchThemes(filters),
      fetchSentiment(filters),
      fetchCompare(filters, 'programme'),
    ])
    setIsLive(healthy)
    setThemes(themeData)
    setSentiment(sentimentData)
    setCompare(compareData)
    setLoading(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey])

  useEffect(() => { refresh() }, [refresh])

  return { themes, sentiment, compare, isLive, loading, refresh }
}
