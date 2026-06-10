import { useMemo, useState, useEffect } from 'react'
import { Link, NavLink, useLocation, useParams, useNavigate } from 'react-router-dom'
import { getFilteredThemes } from '../data/themes'
import { useThemeSummary } from '../hooks/useThemeSummary'
import FilterDropdown from '../components/FilterDropdown'
import { CITY_TO_BRIN, LOCATION_OPTIONS } from '../constants/locations'

function normaliseComment(comment) {
  return String(comment || '').replace(/^"+|"+$/g, '')
}

function subthemeTokens(subtheme) {
  const stopwords = new Set(['and', 'the', 'for', 'with', 'from', 'that', 'this', 'over', 'into'])
  return String(subtheme || '')
    .toLowerCase()
    .match(/[a-z0-9]+/g)
    ?.filter((token) => token.length > 3 && !stopwords.has(token)) ?? []
}

function buildSubthemeRows(subthemes, apiRows, sourceComments) {
  if (apiRows?.length > 0) {
    return apiRows.map((row) => {
      const percentage = Number(row.percentage)
      const mentions = Number(row.mentions)

      return {
        subtheme: row.subtheme,
        percentage: Number.isFinite(percentage) ? percentage : 0,
        mentions: Number.isFinite(mentions) ? mentions : 0,
        docPercentage: Number.isFinite(Number(row.doc_percentage)) ? Number(row.doc_percentage) : null,
      }
    })
  }

  const comments = sourceComments.map((comment) => String(comment).toLowerCase()).filter(Boolean)
  const rows = subthemes.map((subtheme) => {
    const tokens = subthemeTokens(subtheme)
    const mentions = comments.filter((comment) =>
      tokens.some((token) => comment.includes(token) || comment.includes(token.slice(0, 6))),
    ).length

    return {
      subtheme,
      mentions,
      docPercentage: comments.length > 0 ? Math.round((mentions / comments.length) * 100) : 0,
      percentage: 0,
    }
  })
  const totalMentions = rows.reduce((sum, row) => sum + row.mentions, 0)
  return rows.map((row) => ({
    ...row,
    percentage: totalMentions > 0 ? Math.round((row.mentions / totalMentions) * 100) : 0,
  }))
}

function CommentCard({ comment }) {
  const [expanded, setExpanded] = useState(false)
  const text = normaliseComment(comment)
  const isLong = text.length > 180
  const displayText = expanded ? text : (isLong ? text.slice(0, 170) + '...' : text)

  return (
    <div
      onClick={() => isLong && setExpanded(!expanded)}
      className={`bg-surface border border-outline-variant/10 rounded-xl p-4 flex flex-col justify-between shadow-sm transition-all duration-200 ${
        isLong ? 'cursor-pointer select-none hover:border-primary/20' : ''
      }`}
    >
      <blockquote className="text-sm text-on-surface-variant leading-relaxed italic">
        "{displayText}"
      </blockquote>
      {isLong && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            setExpanded(!expanded)
          }}
          className="mt-3 flex items-center gap-1 text-[11px] font-bold text-primary hover:text-primary-variant transition-colors self-end uppercase tracking-wider"
        >
          {expanded ? 'Show Less' : 'Show More'}
          <span className="material-symbols-outlined text-xs">
            {expanded ? 'keyboard_arrow_up' : 'keyboard_arrow_down'}
          </span>
        </button>
      )}
    </div>
  )
}

function CommentColumn({ title, icon, tone, comments }) {
  const toneClass = {
    positive: 'border-tertiary-container bg-green-50 text-green-950',
    critical: 'border-error bg-red-50 text-red-950',
    suggestion: 'border-secondary bg-blue-50 text-blue-950',
  }[tone]

  const iconClass = {
    positive: 'text-green-700',
    critical: 'text-red-700',
    suggestion: 'text-secondary',
  }[tone]

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-5 shadow-ambient border border-outline-variant/10">
      <div className="flex items-center gap-2 mb-4">
        <span className={`material-symbols-outlined text-xl ${iconClass}`}>{icon}</span>
        <h2 className="text-base font-bold font-headline text-primary">{title}</h2>
      </div>
      <div className="space-y-3">
        {comments.length > 0 ? (
          comments.slice(0, 3).map((comment, i) => (
            <blockquote
              key={i}
              className={`p-4 rounded-xl border-l-4 italic text-sm leading-relaxed ${toneClass}`}
            >
              {normaliseComment(comment)}
            </blockquote>
          ))
        ) : (
          <p className="text-sm text-on-surface-variant bg-surface p-4 rounded-xl">
            No comments returned for this group yet.
          </p>
        )}
      </div>
    </div>
  )
}

function SuggestionSection({ suggestions }) {
  return (
    <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-secondary text-xl">lightbulb</span>
          <h2 className="text-base md:text-lg font-bold font-headline text-primary">Student Suggestions</h2>
        </div>
        <span className="text-[10px] uppercase tracking-wider font-bold text-on-surface-variant">
          Solution-oriented
        </span>
      </div>

      {suggestions.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {suggestions.slice(0, 3).map((suggestion, i) => (
            <blockquote
              key={i}
              className="bg-blue-50 p-4 rounded-xl border-l-4 border-secondary italic text-sm text-blue-955 leading-relaxed"
            >
              {normaliseComment(suggestion)}
            </blockquote>
          ))}
        </div>
      ) : (
        <p className="text-sm text-on-surface-variant bg-surface p-4 rounded-xl">
          No clear solution-oriented student suggestions were returned for this theme yet.
        </p>
      )}
    </div>
  )
}

function DonutChart({ rows, title }) {
  if (!rows || rows.length === 0) return null

  const radius = 50
  const strokeWidth = 14
  const circ = 2 * Math.PI * radius // ~314.16

  let currentOffset = 0
  const colors = ['#002F59', '#006A6A', '#3C8D8D', '#727781', '#A9A9A9', '#C2C6D1']

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/10 shadow-sm flex flex-col items-center gap-4">
      <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant w-full text-left">
        {title || 'Breakdown'}
      </h3>
      <div className="relative w-[140px] h-[140px] flex items-center justify-center">
        <svg width="140" height="140" viewBox="0 0 140 140" className="transform -rotate-90">
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="transparent"
            stroke="#E6E8EE"
            strokeWidth={strokeWidth}
          />
          {rows.map((row, idx) => {
            const pct = row.percentage || 0
            if (pct <= 0) return null
            const strokeLength = (pct / 100) * circ
            const offset = currentOffset
            currentOffset += strokeLength
            const color = colors[idx % colors.length]

            return (
              <circle
                key={row.subtheme}
                cx="70"
                cy="70"
                r={radius}
                fill="transparent"
                stroke={color}
                strokeWidth={strokeWidth}
                strokeDasharray={`${strokeLength} ${circ}`}
                strokeDashoffset={-offset}
                strokeLinecap="round"
                className="transition-all duration-500 hover:stroke-[16px] cursor-pointer"
                title={`${row.subtheme}: ${row.percentage}%`}
              />
            )
          })}
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-[9px] uppercase font-bold text-on-surface-variant/50">Total</span>
          <span className="text-lg font-extrabold font-headline text-primary">
            {rows.reduce((sum, r) => sum + (r.mentions || 0), 0)}
          </span>
          <span className="text-[9px] text-on-surface-variant/70">mentions</span>
        </div>
      </div>

      {/* Legend */}
      <div className="w-full space-y-2 mt-2 max-h-[160px] overflow-y-auto pr-1">
        {rows.map((row, idx) => {
          const color = colors[idx % colors.length]
          return (
            <div key={row.subtheme} className="flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2 truncate">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
                <span className="text-on-surface-variant truncate font-medium">{row.subtheme}</span>
              </div>
              <span className="font-bold text-primary shrink-0">{row.percentage}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function SubthemesList({ rows, onSelectSubtheme, activeSubtheme }) {
  const hasRows = rows.length > 0

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
          Key Sub-themes Detected
        </h2>
        <span className="material-symbols-outlined text-outline text-xl">layers</span>
      </div>

      {hasRows ? (
        <div className="flex flex-col gap-2.5">
          {rows.map((row) => {
            const isActive = activeSubtheme === row.subtheme
            return (
              <button
                key={row.subtheme}
                onClick={() => onSelectSubtheme(row.subtheme)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all duration-200 flex flex-col gap-2 group ${
                  isActive
                    ? 'bg-primary border-primary text-white shadow-md'
                    : 'bg-surface-container-low hover:bg-surface-container-high border-outline-variant/10 text-on-surface hover:scale-[1.01]'
                }`}
              >
                <div className="flex justify-between items-center w-full gap-2">
                  <span
                    className={`text-sm font-bold truncate ${
                      isActive ? 'text-white' : 'text-primary group-hover:text-primary-variant'
                    }`}
                  >
                    {row.subtheme}
                  </span>
                  <span
                    className={`text-xs font-bold shrink-0 ${
                      isActive ? 'text-white/90' : 'text-on-surface-variant'
                    }`}
                  >
                    {row.percentage}%
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-surface-container overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isActive ? 'bg-white' : 'bg-primary'
                    }`}
                    style={{ width: `${row.percentage > 0 ? Math.max(2, Math.min(100, row.percentage)) : 0}%` }}
                  />
                </div>
                <div
                  className={`flex justify-between items-center w-full text-[10px] ${
                    isActive ? 'text-white/80' : 'text-on-surface-variant/85 font-medium'
                  }`}
                >
                  <span>{row.mentions} comments</span>
                  <span className="flex items-center gap-0.5 uppercase tracking-wider font-semibold">
                    Drill down <span className="material-symbols-outlined text-[10px]">chevron_right</span>
                  </span>
                </div>
              </button>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-on-surface-variant">No subthemes returned yet.</p>
      )}
    </div>
  )
}

export default function ViewMorePage() {
  const { id, subthemeName } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  const decodedSubtheme = useMemo(() => {
    return subthemeName ? decodeURIComponent(subthemeName) : null
  }, [subthemeName])

  const [filters, setFilters] = useState(() => {
    const sf = location.state?.filters
    return {
      jaar: sf?.jaar ?? 'All',
      locatie: sf?.locatie ?? 'All',
      opleiding: sf?.opleiding ?? 'All',
      studievorm: sf?.studievorm ?? 'All',
      taal: sf?.taal ?? 'All',
    }
  })

  const [filterOptions, setFilterOptions] = useState({
    academic_years: [],
    programmes: [],
    study_modes: [],
    languages: [],
  })

  useEffect(() => {
    fetch('http://localhost:5001/api/filter-options')
      .then((r) => r.json())
      .then((data) => {
        if (data.status === 'success') setFilterOptions(data.options)
      })
      .catch(() => {})
  }, [])

  const [filteredPercentage, setFilteredPercentage] = useState(null)

  function setFilter(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  function clearFilters() {
    setFilters({ jaar: 'All', locatie: 'All', opleiding: 'All', studievorm: 'All', taal: 'All' })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v !== 'All')

  const fallbackTheme = useMemo(() => {
    const themes = getFilteredThemes({
      jaar: 'All',
      locatie: 'All',
      opleiding: 'All',
      studievorm: 'All',
      cohort: 'All',
    })
    return themes.find((t) => t.id === id)
  }, [id])

  const theme = location.state?.theme?.id === id ? location.state.theme : fallbackTheme
  const { liveData, loadingLive } = useThemeSummary(theme, filters)

  useEffect(() => {
    if (!theme) return
    const params = new URLSearchParams()
    if (filters.jaar !== 'All') params.append('academic_year', filters.jaar)
    if (filters.locatie !== 'All')
      params.append('location', CITY_TO_BRIN[filters.locatie] || filters.locatie)
    if (filters.opleiding !== 'All') params.append('programme', filters.opleiding)
    if (filters.studievorm !== 'All') params.append('study_mode', filters.studievorm)
    if (filters.taal !== 'All') params.append('language', filters.taal)
    fetch(`http://localhost:5001/api/themes-overview?${params}`)
      .then((r) => r.json())
      .then((data) => {
        const d = data[theme.name]
        setFilteredPercentage(d && typeof d.frequency === 'number' ? d.frequency : null)
      })
      .catch(() => setFilteredPercentage(null))
  }, [filters, theme?.name])

  // FIX: Safe error-state handling, if liveData fails/offline, fall back to mock theme!
  const hasLlmError = !liveData || liveData.error || liveData.status === 'error'
  const effectiveData = hasLlmError ? (theme.cachedInsight || theme) : liveData

  // Drilldown data logic: checks if subthemeName is present in params
  const activeData = useMemo(() => {
    if (!theme) return null

    const cached = effectiveData || theme

    if (decodedSubtheme && cached.subtheme_data && cached.subtheme_data[decodedSubtheme]) {
      const subData = cached.subtheme_data[decodedSubtheme]
      return {
        isSubtheme: true,
        name: decodedSubtheme,
        summary: subData.summary,
        subthemes: subData.subthemes || [],
        subtheme_mentions: subData.subtheme_mentions || [],
        quotes: subData.quotes || [],
        positive_comments: [],
        critical_comments: [],
        student_suggestions: [],
      }
    }

    const comments = cached.quotes?.length > 0 ? cached.quotes : theme.quotes ?? []
    const subthemes = cached.subthemes?.length > 0 ? cached.subthemes : theme.subthemes ?? []
    const positiveComments = cached.positive_comments?.length > 0 ? cached.positive_comments : []
    const criticalComments = cached.critical_comments?.length > 0 ? cached.critical_comments : []
    const studentSuggestions = cached.student_suggestions?.length > 0 ? cached.student_suggestions : []

    const chartRows = buildSubthemeRows(
      subthemes,
      cached.subtheme_mentions,
      [...comments, ...positiveComments, ...criticalComments, ...studentSuggestions],
    )

    return {
      isSubtheme: false,
      name: theme.name,
      summary: cached.summary || theme.aiSummary,
      subthemes: subthemes,
      subtheme_mentions: chartRows,
      quotes: comments,
      positive_comments: positiveComments,
      critical_comments: criticalComments,
      student_suggestions: studentSuggestions,
    }
  }, [theme, effectiveData, decodedSubtheme])

  if (!theme) {
    return (
      <main className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-10">
        <p className="text-on-surface-variant">Theme not found.</p>
        <NavLink to="/" className="text-sm text-primary font-semibold mt-4 inline-block">
          Back to overview
        </NavLink>
      </main>
    )
  }

  return (
    <main className="bg-surface min-h-[calc(100svh-64px)] font-sans">
      <div className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-10">
        {/* Breadcrumb Navigation */}
        <div className="flex flex-wrap items-center gap-1 text-sm font-semibold text-primary/70 mb-6">
          <Link to="/" className="hover:text-primary transition-colors flex items-center gap-1">
            <span className="material-symbols-outlined text-base">home</span>
            Overview
          </Link>
          <span className="material-symbols-outlined text-xs text-outline select-none">chevron_right</span>
          {decodedSubtheme ? (
            <>
              <button
                onClick={() => navigate(`/thema/${theme.id}`, { state: { theme, filters } })}
                className="hover:text-primary transition-colors focus:outline-none bg-transparent border-none p-0 cursor-pointer font-semibold text-primary/70"
              >
                {theme.name}
              </button>
              <span className="material-symbols-outlined text-xs text-outline select-none">chevron_right</span>
              <span className="text-primary font-bold">{decodedSubtheme}</span>
            </>
          ) : (
            <span className="text-primary font-bold">{theme.name}</span>
          )}
        </div>

        {/* Filters bar */}
        <div className="relative z-20 bg-surface-container-lowest/85 glass-panel shadow-editorial rounded-2xl px-5 py-4 mb-6">
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
              className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-on-surface-variant hover:text-primary transition-colors border-none bg-transparent cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">filter_alt_off</span>
              Clear all filters
            </button>
          )}
        </div>

        {/* Theme Header */}
        <section
          className="rounded-2xl overflow-hidden shadow-ambient border border-outline-variant/10 text-white"
          style={{ background: 'linear-gradient(135deg, #002F59 0%, #00467F 100%)' }}
        >
          <div className="p-5 md:p-8">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
              <div className="flex items-start gap-4">
                <span
                  className="material-symbols-outlined text-4xl md:text-5xl shrink-0"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  {theme.icon}
                </span>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-white/70 mb-1">
                    {activeData.isSubtheme ? `Sub-theme of ${theme.name}` : 'Theme detail'}
                  </p>
                  <h1 className="text-2xl md:text-4xl font-bold font-headline leading-tight">
                    {activeData.name}
                  </h1>
                  {!activeData.isSubtheme && theme.subtag && (
                    <p className="text-sm text-white/75 mt-2">{theme.subtag}</p>
                  )}
                  {activeData.isSubtheme && (
                    <button
                      onClick={() => navigate(`/thema/${theme.id}`, { state: { theme, filters } })}
                      className="mt-3 inline-flex items-center gap-1 text-xs text-white/80 hover:text-white bg-white/10 hover:bg-white/20 px-2.5 py-1 rounded transition-colors font-medium border-none cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
                      Back to Parent Theme
                    </button>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {loadingLive && (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-white/80">
                    <span className="w-2 h-2 rounded-full bg-white/80 animate-pulse" />
                    Loading insights
                  </span>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Main Content Grid */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-5 md:gap-6 mt-6">
          <div className="lg:col-span-8 space-y-5">
            {/* Summary Box */}
            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 md:p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-blue-600">psychology</span>
                  <h2 className="text-sm font-bold text-blue-900">
                    {activeData.isSubtheme ? 'Gemma 4 Sub-theme Insights' : 'Gemma 4 Insights'}
                  </h2>
                </div>
              </div>

              {loadingLive ? (
                <div className="space-y-3 py-2">
                  <div className="h-3 bg-blue-200/50 rounded animate-pulse w-full" />
                  <div className="h-3 bg-blue-200/50 rounded animate-pulse w-11/12" />
                  <div className="h-3 bg-blue-200/50 rounded animate-pulse w-4/6" />
                </div>
              ) : hasLlmError ? (
                <>
                  <div className="p-3 bg-amber-50 text-amber-800 text-xs rounded-xl border border-amber-200 mb-3">
                    LLM offline — showing unfiltered cached insights. Start llama-server to generate filtered
                    analysis.
                  </div>
                  {activeData.summary ? (
                    <p className="text-sm md:text-base text-blue-900 leading-relaxed bg-white/60 p-4 rounded-xl border border-blue-100/60">
                      {activeData.summary}
                    </p>
                  ) : (
                    <p className="text-sm text-blue-900/60 italic">No cached summary available.</p>
                  )}
                </>
              ) : (
                <p className="text-sm md:text-base text-blue-900 leading-relaxed bg-white/60 p-4 rounded-xl border border-blue-100/60">
                  {activeData.summary}
                </p>
              )}
            </div>

            {/* Main theme positive/critical columns (only visible when not drilled down) */}
            {!activeData.isSubtheme && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <CommentColumn
                  title="Top 3 Positive Comments"
                  icon="thumb_up"
                  tone="positive"
                  comments={activeData.positive_comments}
                />
                <CommentColumn
                  title="Top 3 Critical Comments"
                  icon="priority_high"
                  tone="critical"
                  comments={activeData.critical_comments}
                />
              </div>
            )}

            {!activeData.isSubtheme && (
              <SuggestionSection suggestions={activeData.student_suggestions} />
            )}

            {/* Scrollable Comments Grid (populated with up to 100 comments) */}
            {activeData.quotes.length > 0 && (
              <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div className="flex flex-col">
                    <h2 className="text-base md:text-lg font-bold font-headline text-primary">
                      Retrieved Student Comments
                    </h2>
                    <p className="text-xs text-on-surface-variant/60 mt-0.5">
                      Showing up to {activeData.quotes.length} comments from anonymized survey database
                    </p>
                  </div>
                  <span className="material-symbols-outlined text-outline text-xl">format_quote</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                  {activeData.quotes.map((comment, i) => (
                    <CommentCard key={i} comment={comment} />
                  ))}
                </div>
                <p className="text-[10px] text-on-surface-variant/50 italic mt-4">
                  * Verbatim quotes retrieved from vector database offline. Scroll vertically to view more.
                  Expand cards to view long comments.
                </p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside className="lg:col-span-4 space-y-5">
            {/* SVG Pie Chart replacing the percentage StatTile */}
            <DonutChart
              rows={activeData.subtheme_mentions}
              title={activeData.isSubtheme ? 'Sub-subtheme breakdown' : 'Sub-theme mentions breakdown'}
            />

            {/* List of subthemes as buttons */}
            {!activeData.isSubtheme ? (
              <SubthemesList
                rows={activeData.subtheme_mentions}
                onSelectSubtheme={(subName) => navigate(`/thema/${theme.id}/subtheme/${encodeURIComponent(subName)}`, { state: { theme, filters } })}
                activeSubtheme={decodedSubtheme}
              />
            ) : (
              <div className="space-y-5">
                {/* List of other subthemes to easily switch from subtheme page */}
                <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                    Other Sub-themes
                  </h3>
                  <div className="flex flex-col gap-2.5">
                    {theme.subtheme_mentions?.filter(sm => sm.subtheme !== decodedSubtheme).map((sm) => (
                      <button
                        key={sm.subtheme}
                        onClick={() => navigate(`/thema/${theme.id}/subtheme/${encodeURIComponent(sm.subtheme)}`, { state: { theme, filters } })}
                        className="w-full text-left p-3.5 rounded-xl border border-outline-variant/10 bg-surface-container-low hover:bg-surface-container-high text-sm font-bold text-primary transition-all duration-200 hover:scale-[1.01] cursor-pointer"
                      >
                        <div className="flex justify-between items-center w-full gap-2">
                          <span className="truncate">{sm.subtheme}</span>
                          <span className="text-xs font-bold text-on-surface-variant shrink-0">{sm.percentage}%</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sub-subtheme tags list */}
                <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                    Drilled Down Sub-themes
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {activeData.subthemes.map((st, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 bg-surface-container-low rounded-full text-xs font-semibold text-on-surface shadow-sm border border-outline-variant/5"
                      >
                        {st}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={() => navigate(`/thema/${theme.id}`, { state: { theme, filters } })}
                    className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl border border-primary text-primary hover:bg-primary/5 text-xs font-bold py-2.5 transition-colors cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-sm">arrow_upward</span>
                    Reset to Main Theme
                  </button>
                </div>
              </div>
            )}

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-primary text-white text-sm font-bold px-4 py-3 hover:bg-primary/90 transition-colors shadow-sm"
            >
              <span className="material-symbols-outlined text-base">dashboard</span>
              Return to dashboard
            </Link>
          </aside>
        </section>
      </div>
    </main>
  )
}
