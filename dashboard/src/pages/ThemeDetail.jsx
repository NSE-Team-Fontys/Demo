import { useMemo } from 'react'
import { useParams, NavLink, Link, useNavigate } from 'react-router-dom'
import { getFilteredThemes, FILTER_OPTIONS, OPLEIDING_PROFILES } from '../data/themes'
import TrendChart from '../components/TrendChart'

// ── Donut chart (inlined, larger than the drawer version) ──────────────────
function DonutChart({ breakdown, score }) {
  const size = 120
  const r = 48
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r

  const segments = [
    { value: breakdown.positive, color: '#005119' },
    { value: breakdown.neutral,  color: '#b45309' },
    { value: breakdown.negative, color: '#ba1a1a' },
  ]

  let offset = 0
  const arcs = segments.map((seg) => {
    const dash = (seg.value / 100) * circumference
    const arc = { ...seg, dash, offset }
    offset += dash
    return arc
  })

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
      <circle cx={cx} cy={cy} r={r} fill="transparent" stroke="#e7e8e9" strokeWidth="10" />
      {arcs.map((arc, i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill="transparent"
          stroke={arc.color}
          strokeWidth="10"
          strokeDasharray={`${arc.dash} ${circumference - arc.dash}`}
          strokeDashoffset={-arc.offset}
        />
      ))}
    </svg>
  )
}

// ── Sentiment badge ─────────────────────────────────────────────────────────
const BADGE = {
  positive: 'bg-tertiary-container text-white',
  neutral:  'bg-orange-200 text-orange-900',
  critical: 'bg-error-container text-on-error-container',
}
const BADGE_LABEL = {
  positive: 'Positive',
  neutral:  'Neutral',
  critical: 'Critical',
}

// ── Bar colour by score threshold ────────────────────────────────────────────
function barColor(score) {
  if (score >= 65) return '#005119'
  if (score >= 38) return '#b45309'
  return '#ba1a1a'
}

// ── Per-opleiding horizontal bar chart ──────────────────────────────────────
function OpleidingBars({ themeId }) {
  const opleidingen = FILTER_OPTIONS.opleiding

  const rows = opleidingen.map((opl) => {
    const profile = OPLEIDING_PROFILES[opl]
    const data = profile ? profile[themeId] : null
    const score = data ? data.sentimentScore : 0
    return { opl, score }
  })

  return (
    <div className="space-y-3">
      {rows.map(({ opl, score }) => (
        <div key={opl} className="flex items-center gap-3">
          <span className="text-xs text-on-surface-variant w-28 md:w-40 shrink-0 truncate">{opl}</span>
          <div className="flex-1 bg-surface-container rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${score}%`, background: barColor(score) }}
            />
          </div>
          <span className="text-xs font-semibold text-on-surface w-8 text-right">{score}%</span>
        </div>
      ))}
    </div>
  )
}

// ── Sub-themes with static proportional bars ────────────────────────────────
function SubThemeBars({ subthemes }) {
  // Distribute 100% roughly evenly with slight variation
  const total = subthemes.length
  const base = Math.floor(100 / total)
  const proportions = subthemes.map((_, i) => {
    if (i === 0) return base + (100 - base * total)
    return base
  })

  // Running cumulative widths to give visual variety
  const tweaked = proportions.map((p, i) => {
    const offsets = [0, 8, -5, 10, -3, 6]
    return Math.max(15, Math.min(85, p + (offsets[i % offsets.length] || 0)))
  })

  return (
    <div className="space-y-2">
      {subthemes.map((st, i) => (
        <div key={st} className="flex items-center gap-3">
          <span className="text-xs text-on-surface-variant w-24 md:w-36 shrink-0">{st}</span>
          <div className="flex-1 bg-surface-container rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full rounded-full bg-primary/50"
              style={{ width: `${tweaked[i]}%` }}
            />
          </div>
          <span className="text-[10px] text-on-surface-variant w-6 text-right">{tweaked[i]}%</span>
        </div>
      ))}
    </div>
  )
}

// ── Related themes (closest percentage) ─────────────────────────────────────
function RelatedThemeCard({ theme }) {
  const styles = {
    positive: { bg: 'bg-tertiary-container/20', border: 'border-tertiary-container/30', icon: 'text-tertiary-container' },
    neutral:  { bg: 'bg-orange-50', border: 'border-orange-200/40', icon: 'text-orange-500' },
    critical: { bg: 'bg-error-container/20', border: 'border-error/20', icon: 'text-error' },
  }[theme.sentiment]

  return (
    <Link
      to={`/thema/${theme.id}`}
      className={`flex items-center gap-3 p-3 rounded-xl border ${styles.bg} ${styles.border} hover:scale-[1.02] transition-transform`}
    >
      <span
        className={`material-symbols-outlined text-xl ${styles.icon}`}
        style={{ fontVariationSettings: "'FILL' 1" }}
      >
        {theme.icon}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold text-primary truncate">{theme.name}</p>
        <p className="text-[10px] text-on-surface-variant">{theme.percentage}% of responses</p>
      </div>
      <span className="text-xs text-on-surface-variant">→</span>
    </Link>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function ThemeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const defaultFilters = {
    opleiding: 'Software Engineering',
    studievorm: 'All',
    locatie: 'All locations',
  }

  const allThemes = useMemo(() => getFilteredThemes(defaultFilters), [])
  const theme = useMemo(() => allThemes.find((t) => t.id === id), [allThemes, id])

  const relatedThemes = useMemo(() => {
    if (!theme) return []
    return [...allThemes]
      .filter((t) => t.id !== theme.id)
      .sort((a, b) => Math.abs(a.percentage - theme.percentage) - Math.abs(b.percentage - theme.percentage))
      .slice(0, 3)
  }, [allThemes, theme])

  if (!theme) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-10">
        <p className="text-on-surface-variant">Theme not found.</p>
        <NavLink to="/" className="text-sm text-primary font-semibold mt-4 inline-block">
          ← Back to overview
        </NavLink>
      </div>
    )
  }

  const iconStyle = {

    positive: 'text-tertiary-container',
    neutral:  'text-orange-400',
    critical: 'text-error',
  }[theme.sentiment]

  return (
    <div className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-10">

      {/* Back button */}
      <NavLink
        to="/"
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary/70 hover:text-primary mb-8 transition-colors"
      >
        <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>
          arrow_back
        </span>
        Back to overview
      </NavLink>

      {/* Hero header */}
      <div className="flex flex-wrap items-center gap-4 mb-6 md:gap-6 md:mb-10">
        <span
          className={`material-symbols-outlined text-4xl md:text-6xl ${iconStyle}`}
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          {theme.icon}
        </span>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl md:text-4xl font-bold font-headline text-primary leading-tight">{theme.name}</h1>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className={`text-xs font-bold px-3 py-1 rounded-full ${BADGE[theme.sentiment]}`}>
              {BADGE_LABEL[theme.sentiment]}
            </span>
            <span className="text-sm text-on-surface-variant">
              Mentioned in <span className="font-bold text-primary">{theme.percentage}%</span> of responses
            </span>
            {theme.subtag && (
              <span className="text-xs text-on-surface-variant/70 italic">{theme.subtag}</span>
            )}
          </div>
        </div>
      </div>

      {/* Two-column grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 md:gap-6">

        {/* LEFT COLUMN */}
        <div className="md:col-span-8 space-y-6">

          {/* AI Samenvatting */}
          <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
            <div className="flex items-center gap-2 mb-3">
              <span
                className="material-symbols-outlined text-base text-secondary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                auto_awesome
              </span>
              <h2 className="text-xs font-bold uppercase tracking-wider text-secondary">
                AI Summary
              </h2>
            </div>
            <p className="text-base text-on-surface leading-relaxed">{theme.aiSummary}</p>
          </div>

          {/* Trend over tijd */}
          <TrendChart activeTheme={theme} allThemes={allThemes} />

          {/* Per opleiding vergelijking */}
          <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base md:text-lg font-bold font-headline text-primary">Comparison by Programme</h2>
              <span className="material-symbols-outlined text-outline text-xl">school</span>
            </div>
            <OpleidingBars themeId={theme.id} />
            <div className="flex gap-4 mt-4 pt-3 border-t border-outline-variant/10">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-2 rounded-sm inline-block" style={{ background: '#005119' }} />
                <span className="text-[10px] text-on-surface-variant">Positive (≥65%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-2 rounded-sm inline-block" style={{ background: '#b45309' }} />
                <span className="text-[10px] text-on-surface-variant">Neutral (38–64%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-2 rounded-sm inline-block" style={{ background: '#ba1a1a' }} />
                <span className="text-[10px] text-on-surface-variant">Critical (&lt;38%)</span>
              </div>
            </div>
          </div>

          {/* Commentaar sectie */}
          <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base md:text-lg font-bold font-headline text-primary">Comments</h2>
              <span className="material-symbols-outlined text-outline text-xl">format_quote</span>
            </div>
            <div className="space-y-4">
              {theme.quotes.map((q, i) => (
                <blockquote
                  key={i}
                  className="bg-surface p-4 rounded-xl border-l-4 border-tertiary-container italic text-sm text-on-surface-variant leading-relaxed"
                >
                  {q}
                </blockquote>
              ))}
            </div>
            <p className="text-[10px] text-on-surface-variant/50 italic mt-4">
              Illustrative examples, not individual student records.
            </p>
          </div>
        </div>

        {/* RIGHT COLUMN — sticky */}
        <div className="md:col-span-4">
          <div className="md:sticky md:top-20 space-y-5">

            {/* Sentiment donut */}
            <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
              <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                Sentiment Score
              </h2>

              <div className="flex flex-col items-center gap-2 mb-4">
                <DonutChart breakdown={theme.sentimentBreakdown} score={theme.sentimentScore} />
                <p className="text-3xl font-extrabold font-headline text-primary">{theme.sentimentScore}%</p>
                <div className="text-center">
                  <p className="text-base font-bold text-on-surface">{theme.sentimentLabel}</p>
                  <p className="text-xs text-on-surface-variant">Sentiment index</p>

                </div>
              </div>
              <div className="flex rounded-full overflow-hidden h-2 gap-px">
                <div
                  className="h-full"
                  style={{ width: `${theme.sentimentBreakdown.positive}%`, background: '#005119' }}
                />
                <div
                  className="h-full"
                  style={{ width: `${theme.sentimentBreakdown.neutral}%`, background: '#d97706' }}
                />
                <div
                  className="h-full"
                  style={{ width: `${theme.sentimentBreakdown.negative}%`, background: '#ba1a1a' }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-on-surface-variant mt-1.5">
                <span>Positive {theme.sentimentBreakdown.positive}%</span>
                <span>Neutral {theme.sentimentBreakdown.neutral}%</span>
                <span>Critical {theme.sentimentBreakdown.negative}%</span>
              </div>
            </div>

            {/* Sub-thema's */}
            <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
              <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                Sub-themes
              </h2>
              <SubThemeBars subthemes={theme.subthemes} />
            </div>

            {/* Gerelateerde thema's */}
            {relatedThemes.length > 0 && (
              <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
                <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                  Related themes
                </h2>
                <div className="space-y-2">
                  {relatedThemes.map((t) => (
                    <RelatedThemeCard key={t.id} theme={t} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
