import { useEffect, useState } from 'react'

export function useThemeSummary(theme) {
  const [liveData, setLiveData] = useState(null)
  const [loadingLive, setLoadingLive] = useState(false)

  useEffect(() => {
    if (!theme) {
      setLiveData(null)
      setLoadingLive(false)
      return
    }

    let isMounted = true

    const fetchLiveSummary = async () => {
      setLoadingLive(true)
      setLiveData(null)
      try {
        const res = await fetch('http://localhost:5001/api/theme-summary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ theme: theme.name, query: theme.name }),
        })
        const data = await res.json()
        if (!isMounted) return

        if (data.status === 'success') {
          setLiveData(data)
        } else {
          setLiveData({ error: data.error || 'Failed to generate summary' })
        }
      } catch (e) {
        console.error('Failed to fetch Gemma 4 summary:', e)
        if (isMounted) setLiveData({ error: 'Failed to connect to backend server.' })
      } finally {
        if (isMounted) setLoadingLive(false)
      }
    }

    fetchLiveSummary()

    return () => {
      isMounted = false
    }
  }, [theme?.id, theme?.name])

  return { liveData, loadingLive }
}
