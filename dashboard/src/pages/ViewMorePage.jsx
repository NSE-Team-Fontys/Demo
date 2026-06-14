import { useMemo, useState, useEffect } from 'react'
import { Link, NavLink, useLocation, useParams, useNavigate } from 'react-router-dom'
import { getFilteredThemes } from '../data/themes'
import { useThemeSummary } from '../hooks/useThemeSummary'
import FilterDropdown from '../components/FilterDropdown'
import { CITY_TO_BRIN, LOCATION_OPTIONS } from '../constants/locations'
import { getThemeColor } from '../constants/themeColors'
import { motion } from 'framer-motion'

function normaliseComment(comment) {
  return String(comment || '').replace(/^"+|"+$/g, '')
}

const INSIGHT_STOPWORDS = new Set([
  'about', 'after', 'again', 'also', 'although', 'because', 'been', 'being', 'between',
  'could', 'from', 'have', 'however', 'into', 'more', 'most', 'other', 'over', 'students',
  'that', 'their', 'there', 'these', 'they', 'this', 'those', 'through', 'under', 'very',
  'while', 'with', 'would', 'waar', 'worden', 'heeft', 'hebben', 'voor', 'door', 'maar',
  'niet', 'zijn', 'deze', 'over', 'meer',
])

function insightTokens(value) {
  return String(value || '')
    .toLowerCase()
    .match(/[a-zA-ZÀ-ÿ0-9]+/g)
    ?.filter((token) => token.length > 3 && !INSIGHT_STOPWORDS.has(token)) ?? []
}

function cleanInsightPoint(value) {
  const cleaned = String(value || '')
    .trim()
    .replace(/^(while|although|however|but|yet)\s+/i, '')
    .replace(/\s+/g, ' ')

  if (!cleaned) return ''
  const capitalized = cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
  return /[.!?]$/.test(capitalized) ? capitalized : `${capitalized}.`
}

function summaryPoints(summary) {
  const sentences = String(summary || '')
    .replace(/\s+/g, ' ')
    .trim()
    .split(/(?<=[.!?])\s+/)
    .filter((sentence) => sentence.length > 20)

  const points = []
  sentences.forEach((sentence) => {
    const leadingContrast = sentence.match(/^(?:while|although)\s+(.{20,}?),\s+(.{20,})$/i)
    const embeddedContrast = sentence.match(/\bwhile\s+(.{20,}?),\s+(.{20,})$/i)
    const joinedContrast = sentence.match(/^(.{20,}?),\s+(?:but|yet|however)\s+(.{20,})$/i)
    const parts = leadingContrast
      ? [leadingContrast[1], leadingContrast[2]]
      : embeddedContrast
        ? [embeddedContrast[1], embeddedContrast[2]]
        : joinedContrast
          ? [joinedContrast[1], joinedContrast[2]]
          : [sentence]

    parts.forEach((part) => {
      const point = cleanInsightPoint(part)
      if (point && !points.includes(point)) points.push(point)
    })
  })

  return points.slice(0, 3)
}

function buildInsightCards(summary, comments) {
  const points = summaryPoints(summary)
  const sourceComments = (comments || [])
    .map(normaliseComment)
    .filter((comment) => comment.length > 1)
  const usedCommentIndexes = new Set()

  return points.map((point, pointIndex) => {
    const pointRoots = new Set(insightTokens(point).map((token) => token.slice(0, 6)))
    const ranked = sourceComments
      .map((comment, commentIndex) => {
        const commentRoots = new Set(insightTokens(comment).map((token) => token.slice(0, 6)))
        const overlap = [...pointRoots].filter((root) => commentRoots.has(root)).length
        const fallbackDistance = (commentIndex - pointIndex * 3 + sourceComments.length) % sourceComments.length
        return { comment, commentIndex, overlap, fallbackDistance }
      })
      .sort((a, b) => b.overlap - a.overlap || a.fallbackDistance - b.fallbackDistance)

    const relatedComments = []
    ranked.forEach((candidate) => {
      if (relatedComments.length >= 3 || usedCommentIndexes.has(candidate.commentIndex)) return
      usedCommentIndexes.add(candidate.commentIndex)
      relatedComments.push(candidate.comment)
    })

    return { point, relatedComments }
  })
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

// ── Comment card with expand/collapse ────────────────────────────────────────
function CommentCard({ comment, accentColor, index = 0 }) {
  const [expanded, setExpanded] = useState(false)
  const text = normaliseComment(comment)
  const isLong = text.length > 180
  const displayText = expanded ? text : (isLong ? text.slice(0, 170) + '...' : text)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: Math.min(index * 0.03, 0.5), ease: [0.16, 1, 0.3, 1] }}
      onClick={() => isLong && setExpanded(!expanded)}
      className={`bg-surface-container-lowest rounded-xl p-4 flex flex-col justify-between shadow-sm transition-all duration-200 border ${
        isLong ? 'cursor-pointer select-none hover:shadow-md' : ''
      }`}
      style={{ borderColor: expanded ? `${accentColor}30` : 'rgba(114,119,129,0.1)' }}
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
          className="mt-3 flex items-center gap-1 text-[11px] font-bold hover:opacity-80 transition-colors self-end uppercase tracking-wider"
          style={{ color: accentColor }}
        >
          {expanded ? 'Show Less' : 'Show More'}
          <span className="material-symbols-outlined text-xs">
            {expanded ? 'keyboard_arrow_up' : 'keyboard_arrow_down'}
          </span>
        </button>
      )}
    </motion.div>
  )
}

// ── Neutral AI findings with expandable source comments ─────────────────────
function InsightBento({ insights, accentColor, gradient, loading, showOfflineNotice, isSubtheme }) {
  const [expandedIndex, setExpandedIndex] = useState(null)

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-3xl p-4 md:p-6 shadow-sm border bg-surface-container-lowest"
      style={{ borderColor: `${accentColor}18` }}
    >
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <span
              className="material-symbols-outlined"
              style={{ color: accentColor, fontVariationSettings: "'FILL' 1" }}
            >
              psychology
            </span>
            <h2 className="text-base md:text-lg font-bold font-headline text-on-surface">
              {isSubtheme ? 'AI sub-theme findings' : 'AI key findings'}
            </h2>
          </div>
          <p className="text-xs text-on-surface-variant/65 mt-1">
            Expand a finding to inspect related verbatim student comments.
          </p>
        </div>
        {!loading && insights.length > 0 && (
          <span
            className="text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-full"
            style={{ color: accentColor, backgroundColor: `${accentColor}0d` }}
          >
            {insights.length} findings
          </span>
        )}
      </div>

      {showOfflineNotice && (
        <div className="p-3 bg-amber-50 text-amber-800 text-xs rounded-xl border border-amber-200 mb-4">
          LLM offline - showing the cached unfiltered analysis.
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="h-64 rounded-2xl skeleton-shimmer md:col-span-2 xl:col-span-1" />
          <div className="space-y-3">
            <div className="h-[122px] rounded-2xl skeleton-shimmer" />
            <div className="h-[122px] rounded-2xl skeleton-shimmer" />
          </div>
        </div>
      ) : insights.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-3 items-stretch">
          {insights.map((insight, index) => {
            const expanded = expandedIndex === index
            const featured = index === 0
            return (
              <motion.article
                layout
                key={insight.point}
                className={`relative overflow-hidden rounded-2xl border p-5 flex flex-col ${
                  featured
                    ? 'md:col-span-2 xl:col-span-3 xl:row-span-2 min-h-[270px] text-white'
                    : 'xl:col-span-3 min-h-[128px]'
                }`}
                style={featured ? {
                  background: gradient,
                  borderColor: 'transparent',
                } : {
                  backgroundColor: `${accentColor}07`,
                  borderColor: `${accentColor}16`,
                }}
              >
                {featured && (
                  <>
                    <div
                      className="absolute inset-0 opacity-[0.08]"
                      style={{
                        backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
                        backgroundSize: '18px 18px',
                      }}
                    />
                    <div className="absolute -right-12 -top-12 w-36 h-36 rounded-full bg-white/10" />
                  </>
                )}

                <div className="relative z-10 flex flex-col h-full">
                  <div className="flex items-center justify-between gap-3 mb-4">
                    <span
                      className={`text-[10px] uppercase tracking-[0.18em] font-bold ${
                        featured ? 'text-white/70' : 'text-on-surface-variant/60'
                      }`}
                    >
                      Finding {String(index + 1).padStart(2, '0')}
                    </span>
                    <span
                      className={`material-symbols-outlined text-lg ${
                        featured ? 'text-white/70' : ''
                      }`}
                      style={featured ? undefined : { color: `${accentColor}90` }}
                    >
                      auto_awesome
                    </span>
                  </div>

                  <p
                    className={`font-headline font-bold leading-relaxed ${
                      featured ? 'text-lg md:text-xl' : 'text-sm md:text-base text-on-surface'
                    }`}
                  >
                    {insight.point}
                  </p>

                  <button
                    type="button"
                    aria-expanded={expanded}
                    onClick={() => setExpandedIndex(expanded ? null : index)}
                    disabled={insight.relatedComments.length === 0}
                    className={`mt-auto pt-5 inline-flex items-center gap-1.5 text-xs font-bold border-none bg-transparent cursor-pointer disabled:cursor-default disabled:opacity-50 ${
                      featured ? 'text-white' : ''
                    }`}
                    style={featured ? undefined : { color: accentColor }}
                  >
                    <span className="material-symbols-outlined text-base">forum</span>
                    {insight.relatedComments.length > 0
                      ? `${expanded ? 'Hide' : 'Read'} ${insight.relatedComments.length} source comments`
                      : 'No source comments available'}
                    <span className="material-symbols-outlined text-base">
                      {expanded ? 'expand_less' : 'expand_more'}
                    </span>
                  </button>

                  {expanded && insight.relatedComments.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-4 space-y-2"
                    >
                      {insight.relatedComments.map((comment, commentIndex) => (
                        <blockquote
                          key={`${index}-${commentIndex}`}
                          className={`rounded-xl p-3 text-xs leading-relaxed italic border ${
                            featured
                              ? 'bg-white/10 border-white/15 text-white/90'
                              : 'bg-white/80 border-outline-variant/10 text-on-surface-variant'
                          }`}
                        >
                          "{comment}"
                        </blockquote>
                      ))}
                    </motion.div>
                  )}
                </div>
              </motion.article>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-on-surface-variant/60 italic">
          No generated summary is available for this selection yet.
        </p>
      )}
    </motion.section>
  )
}

// ── Suggestion section ──────────────────────────────────────────────────────
function SuggestionSection({ suggestions, accentColor }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
      className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10"
    >
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <span
            className="material-symbols-outlined text-xl"
            style={{ color: accentColor, fontVariationSettings: "'FILL' 1" }}
          >
            lightbulb
          </span>
          <h2 className="text-base md:text-lg font-bold font-headline text-on-surface">Student Suggestions</h2>
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
              className="p-4 rounded-xl border-l-4 italic text-sm leading-relaxed"
              style={{
                borderColor: accentColor,
                backgroundColor: `${accentColor}08`,
                color: '#1e293b',
              }}
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
    </motion.div>
  )
}

// ── Donut chart — uses shades of one accent color ───────────────────────────
function DonutChart({ rows, title, accentColor }) {
  if (!rows || rows.length === 0) return null

  const radius = 50
  const strokeWidth = 14
  const circ = 2 * Math.PI * radius
  const shades = [
    accentColor,
    `${accentColor}cc`,
    `${accentColor}99`,
    `${accentColor}66`,
    `${accentColor}44`,
    `${accentColor}30`,
  ]
  const safeRows = rows.map((row) => ({
    ...row,
    percentage: Math.max(0, Number(row.percentage) || 0),
    mentions: Math.max(0, Number(row.mentions) || 0),
  }))
  const percentageTotal = safeRows.reduce((sum, row) => sum + row.percentage, 0)
  const mentionTotal = safeRows.reduce((sum, row) => sum + row.mentions, 0)
  const usePercentages = percentageTotal > 0
  const valueTotal = usePercentages ? percentageTotal : mentionTotal
  let currentOffset = 0
  const segments = safeRows.map((row, index) => {
    const value = usePercentages ? row.percentage : row.mentions
    const normalizedPercentage = valueTotal > 0 ? (value / valueTotal) * 100 : 0
    const segmentLength = (normalizedPercentage / 100) * circ
    const segment = {
      ...row,
      color: shades[index % shades.length],
      normalizedPercentage,
      strokeLength: Math.max(0, segmentLength - 2.5),
      strokeOffset: currentOffset,
    }
    currentOffset += segmentLength
    return segment
  })

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="bg-surface-container-lowest rounded-2xl p-6 border border-outline-variant/10 shadow-sm flex flex-col items-center gap-4"
    >
      <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant w-full text-left">
        {title || 'Breakdown'}
      </h3>
      <div className="relative w-[140px] h-[140px] flex items-center justify-center">
        <svg width="140" height="140" viewBox="0 0 140 140" role="img" aria-label={title || 'Breakdown'}>
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="transparent"
            stroke="#E6E8EE"
            strokeWidth={strokeWidth}
          />
          <g transform="rotate(-90 70 70)">
            {segments.map((segment, index) => (
              <circle
                key={`${segment.subtheme}-${index}`}
                cx="70"
                cy="70"
                r={radius}
                fill="transparent"
                stroke={segment.color}
                strokeWidth={strokeWidth}
                strokeDasharray={`${segment.strokeLength} ${circ - segment.strokeLength}`}
                strokeDashoffset={-segment.strokeOffset}
                strokeLinecap="round"
                className="transition-all duration-500 hover:stroke-[16px] cursor-pointer"
              >
                <title>{`${segment.subtheme}: ${Math.round(segment.normalizedPercentage)}%`}</title>
              </circle>
            ))}
          </g>
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-[9px] uppercase font-bold text-on-surface-variant/50">Total</span>
          <span className="text-lg font-extrabold font-headline" style={{ color: accentColor }}>
            {mentionTotal}
          </span>
          <span className="text-[9px] text-on-surface-variant/70">mentions</span>
        </div>
      </div>

      {/* Legend */}
      <div className="w-full space-y-2 mt-2 max-h-[160px] overflow-y-auto pr-1 custom-scrollbar">
        {segments.map((segment, index) => (
          <div key={`${segment.subtheme}-${index}`} className="flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2 truncate">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: segment.color }} />
              <span className="text-on-surface-variant truncate font-medium">{segment.subtheme}</span>
            </div>
            <span className="font-bold shrink-0" style={{ color: accentColor }}>
              {Math.round(segment.normalizedPercentage)}%
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// ── Subtheme horizontal bar list ────────────────────────────────────────────
function SubthemesList({ rows, onSelectSubtheme, activeSubtheme, accentColor, gradient }) {
  const hasRows = rows.length > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
      className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10"
    >
      <div className="flex items-center justify-between gap-3 mb-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
          Key Sub-themes Detected
        </h2>
        <span className="material-symbols-outlined text-outline text-xl">layers</span>
      </div>

      {hasRows ? (
        <div className="flex flex-col gap-2.5">
          {rows.map((row, idx) => {
            const isActive = activeSubtheme === row.subtheme
            return (
              <motion.button
                key={row.subtheme}
                initial={false}
                onClick={() => onSelectSubtheme(row.subtheme)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all duration-200 flex flex-col gap-2 group cursor-pointer ${
                  isActive
                    ? 'text-white shadow-md'
                    : 'bg-surface-container-low hover:bg-surface-container-high border-outline-variant/10 text-on-surface hover:scale-[1.01]'
                }`}
                style={isActive ? {
                  background: gradient,
                  borderColor: accentColor,
                } : undefined}
              >
                <div className="flex justify-between items-center w-full gap-2">
                  <span
                    className={`text-sm font-bold truncate ${
                      isActive ? 'text-white' : 'text-on-surface'
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
                <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : '#e7e8e9' }}>
                  <motion.div
                    className="h-full rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${row.percentage > 0 ? Math.max(2, Math.min(100, row.percentage)) : 0}%` }}
                    transition={{ duration: 0.6, delay: idx * 0.06 + 0.2, ease: [0.16, 1, 0.3, 1] }}
                    style={{ background: isActive ? '#ffffff' : gradient }}
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
              </motion.button>
            )
          })}
        </div>
      ) : (
        <p className="text-sm text-on-surface-variant">No subthemes returned yet.</p>
      )}
    </motion.div>
  )
}

// ── Quick stats row ─────────────────────────────────────────────────────────
function QuickStats({ activeData, accentColor }) {
  const totalComments = activeData.quotes?.length || 0
  const subthemeCount = activeData.subtheme_mentions?.length || activeData.subthemes?.length || 0
  const suggestionCount = activeData.student_suggestions?.length || 0

  const stats = [
    { icon: 'forum', value: totalComments, label: 'Comments' },
    { icon: 'layers', value: subthemeCount, label: 'Sub-themes' },
    { icon: 'lightbulb', value: suggestionCount, label: 'Suggestions' },
  ]

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map((stat, idx) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 + idx * 0.08, ease: [0.16, 1, 0.3, 1] }}
          className="bg-surface-container-lowest rounded-xl p-4 border border-outline-variant/10 shadow-sm flex flex-col items-center gap-1"
        >
          <span
            className="material-symbols-outlined text-lg"
            style={{ color: accentColor, fontVariationSettings: "'FILL' 1" }}
          >
            {stat.icon}
          </span>
          <span className="text-xl font-extrabold font-headline text-on-surface tabular-nums">
            {stat.value}
          </span>
          <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant/60">
            {stat.label}
          </span>
        </motion.div>
      ))}
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ══════════════════════════════════════════════════════════════════════════════
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
  const colors = theme ? getThemeColor(theme.id) : getThemeColor('content_org')
  const { liveData, loadingLive } = useThemeSummary(theme, filters)

  const [subthemeLiveData, setSubthemeLiveData] = useState(null)
  const [loadingSubtheme, setLoadingSubtheme] = useState(false)

  useEffect(() => {
    if (!decodedSubtheme || !theme) {
      setSubthemeLiveData(null)
      return
    }
    let isMounted = true
    setLoadingSubtheme(true)
    setSubthemeLiveData(null)
    const apiFilters = {}
    if (filters.jaar !== 'All') apiFilters.academic_year = filters.jaar
    if (filters.locatie !== 'All') apiFilters.location = CITY_TO_BRIN[filters.locatie] || filters.locatie
    if (filters.opleiding !== 'All') apiFilters.programme = filters.opleiding
    if (filters.studievorm !== 'All') apiFilters.study_mode = filters.studievorm
    if (filters.taal !== 'All') apiFilters.language = filters.taal
    fetch('http://localhost:5001/api/theme-summary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        theme: theme.name,
        query: decodedSubtheme,
        filters: Object.keys(apiFilters).length > 0 ? apiFilters : undefined,
        allow_model_download: true,
      }),
    })
      .then((r) => r.json())
      .then((data) => { if (isMounted && data.status === 'success') setSubthemeLiveData(data) })
      .catch(() => {})
      .finally(() => { if (isMounted) setLoadingSubtheme(false) })
    return () => { isMounted = false }
  }, [decodedSubtheme, theme?.id, theme?.name, JSON.stringify(filters)])

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
  const effectiveData = hasLlmError ? (theme?.cachedInsight || theme) : liveData

  // Drilldown data logic: checks if subthemeName is present in params
  const activeData = useMemo(() => {
    if (!theme) return null

    const cached = effectiveData || theme

    if (decodedSubtheme && subthemeLiveData) {
      return {
        isSubtheme: true,
        name: decodedSubtheme,
        summary: subthemeLiveData.summary,
        subthemes: subthemeLiveData.subthemes || [],
        subtheme_mentions: subthemeLiveData.subtheme_mentions || [],
        quotes: subthemeLiveData.quotes || [],
        student_suggestions: subthemeLiveData.student_suggestions || [],
      }
    }

    if (decodedSubtheme && !subthemeLiveData) {
      return {
        isSubtheme: true,
        name: decodedSubtheme,
        summary: null,
        subthemes: [],
        subtheme_mentions: [],
        quotes: [],
        student_suggestions: [],
      }
    }

    const comments = cached.quotes?.length > 0 ? cached.quotes : theme.quotes ?? []
    const subthemes = cached.subthemes?.length > 0 ? cached.subthemes : theme.subthemes ?? []
    const studentSuggestions = cached.student_suggestions?.length > 0 ? cached.student_suggestions : []

    const chartRows = buildSubthemeRows(
      subthemes,
      cached.subtheme_mentions,
      [...comments, ...studentSuggestions],
    )

    return {
      isSubtheme: false,
      name: theme.name,
      summary: cached.summary || theme.aiSummary,
      subthemes: subthemes,
      subtheme_mentions: chartRows,
      quotes: comments,
      student_suggestions: studentSuggestions,
    }
  }, [theme, effectiveData, decodedSubtheme, subthemeLiveData])

  const insightCards = useMemo(
    () => buildInsightCards(activeData?.summary, activeData?.quotes),
    [activeData?.summary, activeData?.quotes],
  )
  const displayedComments = useMemo(
    () => activeData?.quotes?.slice(0, 100) || [],
    [activeData?.quotes],
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
    <main className="bg-surface min-h-[calc(100svh-64px)] font-sans">
      <div className="max-w-[1280px] mx-auto px-4 py-6 md:px-8 md:py-10">
        {/* Breadcrumb Navigation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="flex flex-wrap items-center gap-1 text-sm font-semibold text-on-surface-variant/70 mb-6"
        >
          <Link to="/" className="hover:text-on-surface transition-colors flex items-center gap-1 no-underline text-on-surface-variant/70">
            <span className="material-symbols-outlined text-base">home</span>
            Overview
          </Link>
          <span className="material-symbols-outlined text-xs text-outline select-none">chevron_right</span>
          {decodedSubtheme ? (
            <>
              <button
                onClick={() => navigate(`/thema/${theme.id}`, { state: { theme, filters } })}
                className="hover:text-on-surface transition-colors focus:outline-none bg-transparent border-none p-0 cursor-pointer font-semibold text-on-surface-variant/70"
              >
                {theme.name}
              </button>
              <span className="material-symbols-outlined text-xs text-outline select-none">chevron_right</span>
              <span className="font-bold" style={{ color: colors.accent }}>{decodedSubtheme}</span>
            </>
          ) : (
            <span className="font-bold" style={{ color: colors.accent }}>{theme.name}</span>
          )}
        </motion.div>

        {/* Filters bar */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="relative z-20 bg-surface-container-lowest/85 glass-panel shadow-editorial rounded-2xl px-5 py-4 mb-6"
        >
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
        </motion.div>

        {/* ── Theme Header ── */}
        <motion.section
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative rounded-2xl overflow-hidden shadow-editorial border border-outline-variant/10 text-white"
          style={{ background: colors.gradient }}
        >
          {/* Decorative dot pattern */}
          <div
            className="absolute inset-0 opacity-[0.06]"
            style={{
              backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)',
              backgroundSize: '20px 20px',
            }}
          />
          {/* Decorative glow */}
          <div
            className="absolute -top-16 -right-16 w-48 h-48 rounded-full opacity-20"
            style={{ background: 'radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 70%)' }}
          />

          <div className="relative z-10 p-5 md:p-8">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
              <div className="flex items-start gap-4">
                <span
                  className="material-symbols-outlined text-4xl md:text-5xl shrink-0 text-white/90"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  {theme.icon}
                </span>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-white/60 mb-1">
                    {activeData.isSubtheme ? `Sub-theme of ${theme.name}` : 'Theme detail'}
                  </p>
                  <h1 className="text-2xl md:text-4xl font-bold font-headline leading-tight">
                    {activeData.name}
                  </h1>
                  {!activeData.isSubtheme && theme.subtag && (
                    <p className="text-sm text-white/70 mt-2">{theme.subtag}</p>
                  )}
                  {activeData.isSubtheme && (
                    <button
                      onClick={() => navigate(`/thema/${theme.id}`, { state: { theme, filters } })}
                      className="mt-3 inline-flex items-center gap-1 text-xs text-white/80 hover:text-white bg-white/10 hover:bg-white/20 px-2.5 py-1 rounded-lg transition-colors font-medium border-none cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
                      Back to Parent Theme
                    </button>
                  )}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {(loadingLive || loadingSubtheme) && (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-white/80">
                    <span className="w-2 h-2 rounded-full bg-white/80 animate-pulse" />
                    Loading insights
                  </span>
                )}
              </div>
            </div>
          </div>
        </motion.section>

        {/* ── Quick Stats ── */}
        <div className="mt-6">
          <QuickStats activeData={activeData} accentColor={colors.accent} />
        </div>

        {/* ── Main Content Grid ── */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-5 md:gap-6 mt-6">
          <div className="lg:col-span-8 space-y-5">
            <InsightBento
              insights={insightCards}
              accentColor={colors.accent}
              gradient={colors.gradient}
              loading={loadingLive || loadingSubtheme}
              showOfflineNotice={hasLlmError}
              isSubtheme={activeData.isSubtheme}
            />

            {!activeData.isSubtheme && (
              <SuggestionSection suggestions={activeData.student_suggestions} accentColor={colors.accent} />
            )}

            {/* Scrollable Comments Grid */}
            {displayedComments.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10"
              >
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div className="flex flex-col">
                    <h2 className="text-base md:text-lg font-bold font-headline text-on-surface">
                      Retrieved Student Comments
                    </h2>
                    <p className="text-xs text-on-surface-variant/60 mt-0.5">
                      Showing {displayedComments.length} of {activeData.quotes.length} comments from the anonymized survey database
                    </p>
                  </div>
                  <span
                    className="material-symbols-outlined text-xl"
                    style={{ color: `${colors.accent}60` }}
                  >
                    format_quote
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                  {displayedComments.map((comment, i) => (
                    <CommentCard key={i} comment={comment} accentColor={colors.accent} index={i} />
                  ))}
                </div>
                <p className="text-[10px] text-on-surface-variant/50 italic mt-4">
                  * Verbatim quotes retrieved from vector database offline. Scroll vertically to view more.
                  Expand cards to view long comments.
                </p>
              </motion.div>
            )}
          </div>

          {/* ── Sidebar ── */}
          <aside className="lg:col-span-4">
            <div className="space-y-5 lg:sticky lg:top-24">
              {/* SVG Donut Chart */}
              <DonutChart
                rows={activeData.subtheme_mentions}
                title={activeData.isSubtheme ? 'Sub-subtheme breakdown' : 'Sub-theme mentions breakdown'}
                accentColor={colors.accent}
              />

              {/* List of subthemes as buttons */}
              {!activeData.isSubtheme ? (
                <SubthemesList
                  rows={activeData.subtheme_mentions}
                  onSelectSubtheme={(subName) => navigate(`/thema/${theme.id}/subtheme/${encodeURIComponent(subName)}`, { state: { theme, filters } })}
                  activeSubtheme={decodedSubtheme}
                  accentColor={colors.accent}
                  gradient={colors.gradient}
                />
              ) : (
                <div className="space-y-5">
                  {/* List of other subthemes to easily switch from subtheme page */}
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10"
                  >
                    <h3 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                      Other Sub-themes
                    </h3>
                    <div className="flex flex-col gap-2.5">
                      {theme.subtheme_mentions?.filter(sm => sm.subtheme !== decodedSubtheme).map((sm) => (
                        <button
                          key={sm.subtheme}
                          onClick={() => navigate(`/thema/${theme.id}/subtheme/${encodeURIComponent(sm.subtheme)}`, { state: { theme, filters } })}
                          className="w-full text-left p-3.5 rounded-xl border border-outline-variant/10 bg-surface-container-low hover:bg-surface-container-high text-sm font-bold text-on-surface transition-all duration-200 hover:scale-[1.01] cursor-pointer"
                        >
                          <div className="flex justify-between items-center w-full gap-2">
                            <span className="truncate">{sm.subtheme}</span>
                            <span className="text-xs font-bold shrink-0" style={{ color: colors.accent }}>{sm.percentage}%</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </motion.div>

                  {/* Sub-subtheme tags list */}
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                    className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10 space-y-3"
                  >
                    <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                      Drilled Down Sub-themes
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {activeData.subthemes.map((st, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-full text-xs font-semibold text-on-surface shadow-sm border border-outline-variant/5"
                          style={{ backgroundColor: `${colors.accent}08` }}
                        >
                          {st}
                        </span>
                      ))}
                    </div>
                    <button
                      onClick={() => navigate(`/thema/${theme.id}`, { state: { theme, filters } })}
                      className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl border text-xs font-bold py-2.5 transition-colors cursor-pointer hover:opacity-80"
                      style={{ borderColor: colors.accent, color: colors.accent }}
                    >
                      <span className="material-symbols-outlined text-sm">arrow_upward</span>
                      Reset to Main Theme
                    </button>
                  </motion.div>
                </div>
              )}

              <Link
                to="/"
                className="inline-flex items-center justify-center gap-2 w-full rounded-xl text-white text-sm font-bold px-4 py-3 transition-all shadow-sm no-underline hover:opacity-90"
                style={{ background: colors.gradient }}
              >
                <span className="material-symbols-outlined text-base">dashboard</span>
                Return to dashboard
              </Link>
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}
