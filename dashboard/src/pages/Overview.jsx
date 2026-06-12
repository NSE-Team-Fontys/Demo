import { useState, useMemo, useEffect } from 'react'
import { getFilteredThemes, FILTER_OPTIONS } from '../data/themes'
import { mergeWithLiveData } from '../services/api'
import { useApiData } from '../hooks/useApiData'
import { Link } from 'react-router-dom'
import ThemeCard from '../components/ThemeCard'
import TrendChart from '../components/TrendChart'
import ComparisonMiniChart from '../components/ComparisonMiniChart'
import FilterDropdown from '../components/FilterDropdown'
import { LayoutGroup } from 'framer-motion'
import { useVectorDB } from '../context/VectorDBContext'
import { CITY_TO_BRIN, LOCATION_OPTIONS } from '../constants/locations'

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
    jaar: 'All',
    locatie: 'All',
    opleiding: 'All',
    studievorm: 'All',
    cohort: 'All',
    sector: 'All',
    taal: 'All',
  })

  // Fetch filter options on mount
  const [filterOptions, setFilterOptions] = useState({
    academic_years: [],
    locations: [],
    programmes: [],
    study_modes: [],
    cohorts: [],
    sectors: [],
    languages: [],
  });

  useEffect(() => {
    fetch('http://localhost:5001/api/filter-options')
      .then(r => r.json())
      .then(data => {
        if (data.status === 'success') setFilterOptions(data.options);
      })
      .catch(e => console.error(e));
  }, []);

  // 1. Mock / enriched mock data (always available)
  const mockThemes = useMemo(() => getFilteredThemes(filters), [filters])

  // 2. Live API data (may be null when offline)
  const { themes: liveThemes, isLive, loading, refresh } = useApiData(filters)

  // 3. Merge: live data overlays mock where theme IDs match
  const baseThemes = useMemo(
    () => mergeWithLiveData(mockThemes, liveThemes),
    [mockThemes, liveThemes],
  )
  
  const [dynamicThemesData, setDynamicThemesData] = useState({})
  
  // Fetch dynamic theme data and optionally pass filters in the future
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.jaar !== 'All') params.append('academic_year', filters.jaar);
    if (filters.locatie !== 'All') params.append('location', CITY_TO_BRIN[filters.locatie] || filters.locatie);
    if (filters.opleiding !== 'All') params.append('programme', filters.opleiding);
    if (filters.studievorm !== 'All') params.append('study_mode', filters.studievorm);
    if (filters.cohort !== 'All') params.append('cohort', filters.cohort);
    if (filters.taal !== 'All') params.append('language', filters.taal);

    fetch(`http://localhost:5001/api/themes-overview?${params}`)
      .then(r => r.json())
      .then(data => setDynamicThemesData(data))
      .catch(e => console.error(e))
  }, [filters])
  
  const themes = useMemo(() => {
    return baseThemes.map(t => {
      const dynamic = dynamicThemesData[t.name]
      if (dynamic) {
        return {
          ...t,
          percentage: typeof dynamic.frequency === 'number' ? dynamic.frequency : t.percentage,
          responseCount: typeof dynamic.vector_relevant_count === 'number' ? dynamic.vector_relevant_count : null,
          aiSummary: dynamic.summary || t.aiSummary,
          subthemes: dynamic.subthemes?.length > 0 ? dynamic.subthemes : t.subthemes,
          quotes: dynamic.quotes?.length > 0 ? dynamic.quotes : t.quotes,
          cachedInsight: { ...dynamic, status: 'success' },
        }
      }
      return t
    })
  }, [baseThemes, dynamicThemesData])

  // Sort themes by percentage (which is the actual count of comments)
  const sortedThemes = useMemo(() => {
    return [...themes].sort((a, b) => b.percentage - a.percentage)
  }, [themes])

  // Get most popular key subthemes across all themes
  const popularSubthemes = useMemo(() => {
    const list = []
    themes.forEach(t => {
      const mentionsList = t.cachedInsight?.subtheme_mentions || t.subtheme_mentions || []
      mentionsList.forEach(m => {
        list.push({
          name: m.subtheme,
          mentions: m.mentions || 0,
          parentTheme: t
        })
      })
    })
    return list.sort((a, b) => b.mentions - a.mentions).slice(0, 5)
  }, [themes])

  function setFilter(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  function clearFilters() {
    setFilters({ jaar: 'All', locatie: 'All', opleiding: 'All', studievorm: 'All', cohort: 'All', taal: 'All' })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v !== 'All')

  const { vectorData, loading: vectorLoading, error, lastUpdated, refresh: vectorRefresh } = useVectorDB();

  return (
    <main className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-8 flex flex-col gap-6">

      {/* ── Filters bar ── */}
      <div className="relative z-20 bg-surface-container-lowest/85 glass-panel shadow-editorial rounded-2xl px-5 py-4">
        <div className="flex flex-wrap md:flex-nowrap gap-3 flex-1">
          <div className="flex-1 min-w-[130px]">
            <FilterDropdown
              icon="calendar_today"
              label="Academic Year"
              value={filters.jaar}
              options={['All', ...filterOptions.academic_years]}
              onChange={(v) => setFilter('jaar', v)}
            />
          </div>
          <div className="flex-1 min-w-[130px]">
            <FilterDropdown
              icon="location_on"
              label="Location"
              value={filters.locatie}
              options={LOCATION_OPTIONS}
              onChange={(v) => setFilter('locatie', v)}
            />
          </div>
          <div className="flex-1 min-w-[130px]">
            <FilterDropdown
              icon="school"
              label="Programme"
              value={filters.opleiding}
              options={['All', ...filterOptions.programmes]}
              onChange={(v) => setFilter('opleiding', v)}
            />
          </div>
          <div className="flex-1 min-w-[130px]">
            <FilterDropdown
              icon="history_edu"
              label="Study Mode"
              value={filters.studievorm}
              options={['All', ...filterOptions.study_modes]}
              onChange={(v) => setFilter('studievorm', v)}
            />
          </div>
          <div className="flex-1 min-w-[130px]">
            <FilterDropdown
              icon="translate"
              label="Language"
              value={filters.taal}
              options={['All', ...filterOptions.languages]}
              onChange={(v) => setFilter('taal', v)}
            />
          </div>
        </div>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-on-surface-variant hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined text-sm">filter_alt_off</span>
            Clear all filters
          </button>
        )}
      </div>
      <div className="flex flex-col gap-6 md:gap-8 w-full">

        {/* Theme Landscape */}
        <section>
          <div className="flex items-end justify-between mb-5">
            <div>
              <h2 className="text-2xl font-bold font-headline text-primary">
                Theme Frequency Insights
              </h2>
              <p className="text-xs text-tertiary-container mt-0.5">
                Live response frequencies from VectorDB
              </p>
            </div>
          </div>

          <LayoutGroup>
            <div className="flex flex-col gap-6">
              {/* Top 3 themes (Large cards side-by-side) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {sortedThemes.slice(0, 3).map((theme) => (
                  <ThemeCard
                    key={theme.id}
                    theme={theme}
                    size="large"
                    filters={filters}
                  />
                ))}
              </div>

              {/* Remaining themes (Small cards below) */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {sortedThemes.slice(3).map((theme) => (
                  <ThemeCard
                    key={theme.id}
                    theme={theme}
                    size="small"
                    filters={filters}
                  />
                ))}
              </div>
            </div>
          </LayoutGroup>
        </section>

        {/* Most Popular Sub-themes Section */}
        {popularSubthemes.length > 0 && (
          <section className="bg-surface-container-lowest rounded-2xl p-5 shadow-ambient border border-outline-variant/10">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
              <h2 className="text-base font-bold font-headline text-primary">Most Popular Sub-themes</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
              {popularSubthemes.map((sub) => (
                <Link
                  key={sub.name}
                  to={`/thema/${sub.parentTheme.id}`}
                  state={{ theme: sub.parentTheme, filters, selectedSubtheme: sub.name }}
                  onClick={() => window.scrollTo(0, 0)}
                  className="bg-surface-container-low hover:bg-surface-container-high border border-outline-variant/10 rounded-xl p-4 flex flex-col justify-between transition-all duration-300 hover:scale-[1.02] hover:shadow-sm"
                >
                  <div>
                    <span className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-wider block mb-1">
                      {sub.parentTheme.name}
                    </span>
                    <h3 className="text-sm font-bold text-primary line-clamp-2 leading-tight">
                      {sub.name}
                    </h3>
                  </div>
                  <div className="mt-4 flex items-center gap-1.5 text-xs text-on-surface-variant font-semibold">
                    <span className="material-symbols-outlined text-sm text-outline">forum</span>
                    {sub.mentions} comments
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Charts row */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
          <TrendChart activeTheme={null} allThemes={themes} />
          <ComparisonMiniChart theme={themes[0]} filters={filters} />
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


    </main>
  )
}
