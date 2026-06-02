import { useEffect, useState } from 'react'
import { CITY_TO_BRIN } from '../constants/locations'

function buildApiFilters(filters = {}) {
  const map = {
    academic_year: filters.jaar,
    location: filters.locatie ? CITY_TO_BRIN[filters.locatie] || filters.locatie : undefined,
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
    const hasActiveFilters = Object.keys(buildApiFilters(filters)).length > 0
    if (!hasActiveFilters && theme.cachedInsight?.summary) {
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
            allow_model_download: true,
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
