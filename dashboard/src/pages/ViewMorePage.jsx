import { useMemo, useState, useEffect } from 'react'
import { Link, NavLink, useLocation, useParams } from 'react-router-dom'
import { getFilteredThemes } from '../data/themes'
import { useThemeSummary } from '../hooks/useThemeSummary'
import FilterDropdown from '../components/FilterDropdown'

function StatTile({ icon, label, value, helper }) {
  return (
    <div className="bg-surface-container-lowest rounded-xl p-4 border border-outline-variant/10 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <span className="material-symbols-outlined text-primary text-xl">{icon}</span>
        <span className="text-[10px] uppercase tracking-wider font-bold text-on-surface-variant text-right">
          {label}
        </span>
      </div>
      <p className="text-2xl font-extrabold font-headline text-primary mt-3">{value}</p>
      {helper && <p className="text-xs text-on-surface-variant mt-1">{helper}</p>}
    </div>
  )
}

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

function CommentColumn({ title, icon, tone, comments }) {
  const toneClass = {
    positive: 'border-tertiary-container bg-green-50 text-green-950',
    critical: 'border-error bg-red-50 text-red-950',
    suggestion: 'border-secondary bg-blue-50 text-blue-950',
  }[tone]

  const iconClass = {
    positive: 'text-tertiary-container',
    critical: 'text-error',
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
              className="bg-blue-50 p-4 rounded-xl border-l-4 border-secondary italic text-sm text-blue-950 leading-relaxed"
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

function SubthemeMentionChart({ rows }) {
  const hasRows = rows.length > 0

  return (
    <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
          Key Sub-themes Detected
        </h2>
        <span className="material-symbols-outlined text-outline text-xl">monitoring</span>
      </div>

      {hasRows ? (
        <div className="space-y-4">
          {rows.map((row) => (
            <div key={row.subtheme} className="space-y-1.5">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-on-surface truncate">{row.subtheme}</span>
                <span className="text-xs font-bold text-primary shrink-0">{row.percentage}%</span>
              </div>
              <div className="h-2 rounded-full bg-surface-container overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${row.percentage > 0 ? Math.max(2, Math.min(100, row.percentage)) : 0}%` }}
                />
              </div>
              <p className="text-[10px] text-on-surface-variant">
                Mentioned in {row.mentions} retrieved comment{row.mentions === 1 ? '' : 's'}
              </p>
            </div>
          ))}
          <p className="text-[10px] text-on-surface-variant/60">
            Percentages show share of detected subtheme mentions, not sentiment scoring.
          </p>
        </div>
      ) : (
        <p className="text-sm text-on-surface-variant">No subthemes returned yet.</p>
      )}
    </div>
  )
}

export default function ViewMorePage() {
  const { id } = useParams()
  const location = useLocation()

  const [filters, setFilters] = useState({
    jaar: 'All', sector: 'All', opleiding: 'All', studievorm: 'All', taal: 'All',
  })

  const [filterOptions, setFilterOptions] = useState({
    academic_years: [], sectors: [], programmes: [], study_modes: [], languages: [],
  })

  useEffect(() => {
    fetch('http://localhost:5001/api/filter-options')
      .then(r => r.json())
      .then(data => { if (data.status === 'success') setFilterOptions(data.options) })
      .catch(() => {})
  }, [])

  const [filteredPercentage, setFilteredPercentage] = useState(null)

  function setFilter(key, value) {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

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
    if (filters.sector !== 'All') params.append('sector', filters.sector)
    if (filters.opleiding !== 'All') params.append('programme', filters.opleiding)
    if (filters.studievorm !== 'All') params.append('study_mode', filters.studievorm)
    if (filters.taal !== 'All') params.append('language', filters.taal)
    fetch(`http://localhost:5001/api/themes-overview?${params}`)
      .then(r => r.json())
      .then(data => {
        const d = data[theme.name]
        setFilteredPercentage(d && typeof d.frequency === 'number' ? d.frequency : null)
      })
      .catch(() => setFilteredPercentage(null))
  }, [filters, theme?.name])

  const comments = liveData?.quotes?.length > 0 ? liveData.quotes : theme?.quotes ?? []
  const subthemes = liveData?.subthemes?.length > 0 ? liveData.subthemes : theme?.subthemes ?? []
  const summary = liveData?.summary || theme?.aiSummary
  const positiveComments = liveData?.positive_comments?.length > 0 ? liveData.positive_comments : []
  const criticalComments = liveData?.critical_comments?.length > 0 ? liveData.critical_comments : []
  const studentSuggestions = liveData?.student_suggestions?.length > 0 ? liveData.student_suggestions : []
  const chartRows = buildSubthemeRows(
    subthemes,
    liveData?.subtheme_mentions,
    [...comments, ...positiveComments, ...criticalComments, ...studentSuggestions],
  )

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
    <main className="bg-surface min-h-[calc(100svh-64px)]">
      <div className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-10">
        <NavLink
          to="/"
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary/70 hover:text-primary mb-6 transition-colors"
        >
          <span className="material-symbols-outlined text-base">arrow_back</span>
          Back to overview
        </NavLink>

        {/* ── Filters bar ── */}
        <div className="relative z-20 bg-surface-container-lowest/85 glass-panel shadow-editorial rounded-2xl px-5 py-4 mb-6">
          <div className="flex flex-wrap md:flex-nowrap gap-3 flex-1">
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown icon="calendar_today" label="Academic Year" value={filters.jaar}
                options={['All', ...filterOptions.academic_years]} onChange={(v) => setFilter('jaar', v)} />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown icon="category" label="Sector" value={filters.sector}
                options={['All', ...filterOptions.sectors]} onChange={(v) => setFilter('sector', v)} />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown icon="school" label="Programme" value={filters.opleiding}
                options={['All', ...filterOptions.programmes]} onChange={(v) => setFilter('opleiding', v)} />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown icon="history_edu" label="Study Mode" value={filters.studievorm}
                options={['All', ...filterOptions.study_modes]} onChange={(v) => setFilter('studievorm', v)} />
            </div>
            <div className="flex-1 min-w-[130px]">
              <FilterDropdown icon="translate" label="Language" value={filters.taal}
                options={['All', ...filterOptions.languages]} onChange={(v) => setFilter('taal', v)} />
            </div>
          </div>
        </div>

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
                  <p className="text-xs font-bold uppercase tracking-wider text-white/70 mb-1">Theme detail</p>
                  <h1 className="text-2xl md:text-4xl font-bold font-headline leading-tight">{theme.name}</h1>
                  {theme.subtag && <p className="text-sm text-white/75 mt-2">{theme.subtag}</p>}
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

        <section className="grid grid-cols-1 lg:grid-cols-12 gap-5 md:gap-6 mt-6">
          <div className="lg:col-span-8 space-y-5">
            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 md:p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-blue-600">psychology</span>
                  <h2 className="text-sm font-bold text-blue-900">Gemma 4 Insights</h2>
                </div>
              </div>

              {loadingLive ? (
                <div className="space-y-3 py-2">
                  <div className="h-3 bg-blue-200/50 rounded animate-pulse w-full" />
                  <div className="h-3 bg-blue-200/50 rounded animate-pulse w-11/12" />
                  <div className="h-3 bg-blue-200/50 rounded animate-pulse w-4/6" />
                </div>
              ) : liveData?.error ? (
                <div className="p-3 bg-red-50 text-red-700 text-sm rounded-xl border border-red-200">
                  {liveData.error}
                </div>
              ) : (
                <p className="text-sm md:text-base text-blue-900 leading-relaxed bg-white/60 p-4 rounded-xl border border-blue-100/60">
                  {summary}
                </p>
              )}

            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <CommentColumn
                title="Top 3 Positive Comments"
                icon="thumb_up"
                tone="positive"
                comments={positiveComments}
              />
              <CommentColumn
                title="Top 3 Critical Comments"
                icon="priority_high"
                tone="critical"
                comments={criticalComments}
              />
            </div>

            <SuggestionSection suggestions={studentSuggestions} />

            {comments.length > 0 && (
              <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h2 className="text-base md:text-lg font-bold font-headline text-primary">Retrieved Student Comments</h2>
                  <span className="material-symbols-outlined text-outline text-xl">format_quote</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {comments.map((comment, i) => (
                    <blockquote
                      key={i}
                      className="bg-surface p-4 rounded-xl border-l-4 border-blue-500 italic text-sm text-on-surface-variant leading-relaxed shadow-sm"
                    >
                      {normaliseComment(comment)}
                    </blockquote>
                  ))}
                </div>
                <p className="text-[10px] text-on-surface-variant/50 italic mt-4">
                  Actual verbatim quotes retrieved from the database when VectorDB is available.
                </p>
              </div>
            )}
          </div>

          <aside className="lg:col-span-4 space-y-5">
            <StatTile
              icon="bar_chart"
              label="Relevant responses"
              value={`${filteredPercentage ?? theme.percentage}%`}
              helper="Share of responses associated with this theme."
            />

            <SubthemeMentionChart rows={chartRows} />

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-primary text-white text-sm font-bold px-4 py-3 hover:bg-primary/90 transition-colors"
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
