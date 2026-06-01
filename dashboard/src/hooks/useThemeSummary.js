import { useEffect, useState } from 'react'

function buildApiFilters(filters = {}) {
  const map = {
    academic_year: filters.jaar,
    sector: filters.sector,
    programme: filters.opleiding,
    study_mode: filters.studievorm,
    language: filters.taal,
  }
  return Object.fromEntries(Object.entries(map).filter(([, v]) => v && v !== 'All'))
}

export function useThemeSummary(theme, filters = {}) {
  const [liveData, setLiveData] = useState(null)
  const [loadingLive, setLoadingLive] = useState(false)

  const filterKey = JSON.stringify(buildApiFilters(filters))

  useEffect(() => {
    if (!theme) {
      setLiveData(null)
      setLoadingLive(false)
      return
    }

    let isMounted = true
    if (theme.cachedInsight?.summary) {
      setLiveData(theme.cachedInsight)
      setLoadingLive(false)
      return () => {
        isMounted = false
      }
    }

    const fetchLiveSummary = async () => {
      setLoadingLive(true)
      setLiveData(null)
      try {
        const apiFilters = buildApiFilters(filters)
        const res = await fetch('http://localhost:5001/api/theme-summary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            theme: theme.name,
            query: theme.name,
            filters: Object.keys(apiFilters).length > 0 ? apiFilters : undefined,
          }),
        })
        const data = await res.json()
        if (!isMounted) return

        if (data.status === 'success') {
          setLiveData(data)
        } else {
          setLiveData({ error: data.error || 'Failed to generate summary' })
        }
      } catch (e) {
        if (isMounted) setLiveData({ error: 'Failed to connect to backend server.' })
      } finally {
        if (isMounted) setLoadingLive(false)
      }
    }

    fetchLiveSummary()

    return () => {
      isMounted = false
    }
  }, [theme?.id, theme?.name, theme?.cachedInsight, filterKey])

  return { liveData, loadingLive }
}
