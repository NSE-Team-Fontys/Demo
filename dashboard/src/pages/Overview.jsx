import { useState, useMemo } from 'react'
import { getFilteredThemes, FILTER_OPTIONS } from '../data/themes'
import { mergeWithLiveData } from '../services/api'
import { useApiData } from '../hooks/useApiData'
import ThemeCard from '../components/ThemeCard'
import DetailDrawer from '../components/DetailDrawer'
import TrendChart from '../components/TrendChart'
import ComparisonMiniChart from '../components/ComparisonMiniChart'
import FilterDropdown from '../components/FilterDropdown'
import { LayoutGroup } from 'framer-motion'
import { useVectorDB } from '../context/VectorDBContext'

// ── Live/Offline status badge ─────────────────────────────────────────────────
function DataSourceBadge({ isLive, loading, onRefresh }) {
  if (loading) {
    return (
      <span className="flex items-center gap-1.5 text-xs text-on-surface-variant/60 font-medium">
        <span className="w-2 h-2 rounded-full bg-outline/50 animate-pulse" />
        Connecting…
      </span>
    )
  }
  if (isLive) {
    return (
      <button
        onClick={onRefresh}
        title="Click to refresh live data"
        className="flex items-center gap-1.5 text-xs font-semibold text-tertiary-container hover:opacity-80 transition-opacity"
      >
        <span className="w-2 h-2 rounded-full bg-tertiary-container animate-pulse" />
        Live data
        <span className="material-symbols-outlined text-[14px]">refresh</span>
      </button>
    )
  }
  return (
    <button
      onClick={onRefresh}
      title="API offline — click to retry"
      className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant/60 hover:opacity-80 transition-opacity"
    >
      <span className="w-2 h-2 rounded-full bg-outline/40" />
      Demo data
      <span className="material-symbols-outlined text-[14px]">refresh</span>
    </button>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Overview() {
  const [filters, setFilters] = useState({
    jaar:       '2025/2026',
    locatie:    'All locations',
    opleiding:  'Software Engineering',
    studievorm: 'All',
    cohort:     'All',
  })

  // 1. Mock / enriched mock data (always available)
  const mockThemes = useMemo(() => getFilteredThemes(filters), [filters])

  // 2. Live API data (may be null when offline)
  const { themes: liveThemes, isLive, loading, refresh } = useApiData(filters)

  // 3. Merge: live data overlays mock where theme IDs match
  const themes = useMemo(
    () => mergeWithLiveData(mockThemes, liveThemes),
    [mockThemes, liveThemes],
  )

  // Sort by percentage and assign bento sizes dynamically
  const bentoThemes = useMemo(() => {
    const sorted = [...themes].sort((a, b) => b.percentage - a.percentage)
    return sorted.map((t, i) => ({
      ...t,
      size: i === 0 ? 'large' : i <= 2 ? 'medium' : 'small',
    }))
  }, [themes])

  const [activeId, setActiveId] = useState(null)
  const activeTheme = themes.find((t) => t.id === activeId) ?? null

  function setFilter(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  function handleThemeClick(theme) {
    setActiveId((prev) => (prev === theme.id ? null : theme.id))
  }

  const { vectorData, loading: vectorLoading, error, lastUpdated, refresh: vectorRefresh } = useVectorDB();

  return (
    <main className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-8 flex flex-col gap-6">

      {/* ── Filters bar ── */}
      <div className="relative z-20 bg-surface-container-lowest/85 glass-panel shadow-editorial rounded-2xl px-5 py-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="flex flex-wrap md:flex-nowrap gap-3 flex-1">
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown
                icon="calendar_today"
                label="Academic Year"
                value={filters.jaar}
                options={FILTER_OPTIONS.jaar}
                onChange={(v) => setFilter('jaar', v)}
              />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown
                icon="location_on"
                label="Location"
                value={filters.locatie}
                options={FILTER_OPTIONS.locatie}
                onChange={(v) => setFilter('locatie', v)}
              />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown
                icon="school"
                label="Programme"
                value={filters.opleiding}
                options={FILTER_OPTIONS.opleiding}
                onChange={(v) => setFilter('opleiding', v)}
              />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown
                icon="history_edu"
                label="Study Mode"
                value={filters.studievorm}
                options={FILTER_OPTIONS.studievorm}
                onChange={(v) => setFilter('studievorm', v)}
              />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown
                icon="group"
                label="Cohort"
                value={filters.cohort}
                options={FILTER_OPTIONS.cohort}
                onChange={(v) => setFilter('cohort', v)}
              />
            </div>
          </div>

          {/* Live / Offline badge */}
          <div className="shrink-0">
            <DataSourceBadge isLive={isLive} loading={loading} onRefresh={refresh} />
          </div>
        </div>
      </div>

      {/* ── Dashboard grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-8 items-start">

        {/* Left/center — bento + charts */}
        <div className="order-2 md:order-1 col-span-1 md:col-span-8 flex flex-col gap-6 md:gap-8">

          {/* Theme Landscape */}
          <section>
            <div className="flex items-end justify-between mb-5">
              <div>
                <h2 className="text-2xl font-bold font-headline text-primary">
                  Theme Frequency &amp; Sentiment
                </h2>
                {isLive && (
                  <p className="text-xs text-tertiary-container mt-0.5">
                    Enriched with live pipeline data
                  </p>
                )}
              </div>
              <div className="flex gap-3">
                {[
                  { color: '#005119', label: 'Positive' },
                  { color: '#d97706', label: 'Neutral' },
                  { color: '#ba1a1a', label: 'Critical' },
                ].map(({ color, label }) => (
                  <span key={label} className="flex items-center gap-1.5 text-xs font-medium text-on-surface-variant">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                    {label}
                  </span>
                ))}
              </div>
            </div>

            <LayoutGroup>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 auto-rows-fr">
                {bentoThemes.map((theme) => (
                  <ThemeCard
                    key={theme.id}
                    theme={theme}
                    size={theme.size}
                    isActive={activeId === theme.id}
                    onClick={() => handleThemeClick(theme)}
                  />
                ))}
              </div>
            </LayoutGroup>

            {activeTheme && (
              <p className="mt-3 text-xs text-on-surface-variant/50 text-center">
                Click again on a theme to clear the selection
              </p>
            )}
          </section>

          {/* Charts row */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
            <TrendChart activeTheme={activeTheme} allThemes={themes} />
            <ComparisonMiniChart theme={activeTheme ?? themes[0]} filters={filters} />
          </section>

          {/* Live response counts (only shown when API is online) */}
          {isLive && liveThemes && liveThemes.length > 0 && (
            <section className="bg-surface-container-lowest rounded-2xl p-5 shadow-ambient border border-outline-variant/10">
              <div className="flex items-center gap-2 mb-4">
                <span
                  className="material-symbols-outlined text-base text-tertiary-container"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  hub
                </span>
                <h2 className="text-xs font-bold uppercase tracking-wider text-tertiary-container">
                  Live Pipeline — Response Counts
                </h2>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {liveThemes.map((t) => (
                  <div
                    key={t.theme}
                    className="bg-surface-container-low rounded-xl px-3 py-2 flex items-center justify-between gap-2"
                  >
                    <span className="text-xs text-on-surface-variant truncate">{t.theme}</span>
                    <span className="text-sm font-bold text-primary shrink-0">{t.total}</span>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-on-surface-variant/40 mt-3">
                Raw counts from the NSE pipeline database · {new Date().toLocaleTimeString()}
              </p>
            </section>
          )}
        </div>

        {/* Right sidebar — detail drawer */}
        <aside className="order-1 md:order-2 col-span-1 md:col-span-4 flex flex-col gap-5 md:sticky md:top-20">
          <DetailDrawer theme={activeTheme} />

          {!activeTheme && (
            <div className="bg-surface-container-low rounded-2xl p-8 text-center">
              <span className="material-symbols-outlined text-4xl text-outline mb-3 block">
                touch_app
              </span>
              <p className="text-sm text-on-surface-variant">
                Click on a theme to view the details
              </p>
            </div>
          )}
        </aside>
      </div>

      {/* ── Vector DB Section ── */}
      <section className="mt-10">
        <h2 className="text-2xl font-bold mb-4">Vector Database</h2>
        {vectorLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-20 bg-gray-100 rounded"></div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            <div className="flex justify-between items-center">
              <h1 className="text-3xl font-bold">📊 Survey Data Overview</h1>
              <button
                onClick={vectorRefresh}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                🔄 Refresh
              </button>
            </div>

            {error && (
              <div className="p-4 bg-yellow-100 text-yellow-800 rounded border border-yellow-300">
                ⚠️ {error}
              </div>
            )}

            {vectorData.length === 0 ? (
              <div className="p-8 bg-gray-50 rounded border-2 border-dashed text-center">
                <p className="text-gray-600 text-lg">
                  📭 No data yet. Run the <strong>Pipeline Demo</strong> to process survey data.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <p className="text-sm text-gray-700">
                    <strong>Total Documents:</strong> {vectorData.length} entries
                    {lastUpdated && <span className="text-gray-500 ml-4">Last updated: {lastUpdated}</span>}
                  </p>
                </div>

                <div className="grid gap-4">
                  {vectorData.map((item) => (
                    <div 
                      key={item.id}
                      className="p-4 bg-white rounded border border-gray-200 hover:border-blue-400 hover:shadow-md transition"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-sm font-semibold text-gray-600">Entry #{item.id}</span>
                      </div>
                      <p className="text-gray-800 text-sm leading-relaxed mb-2">
                        {item.text}
                      </p>
                      {item.text !== item.full_text && (
                        <details className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                          <summary>Read more...</summary>
                          <p className="mt-2 p-2 bg-gray-50 rounded text-gray-700">
                            {item.full_text}
                          </p>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  )
}
