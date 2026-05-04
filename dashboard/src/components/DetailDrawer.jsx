import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

const SENTIMENT_COLOR = {
  positive: '#005119',
  neutral: '#b45309',
  critical: '#ba1a1a',
}

function DonutChart({ breakdown }) {
  const size = 64
  const r = 26
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r

  const segments = [
    { value: breakdown.positive, color: '#005119' },
    { value: breakdown.neutral, color: '#b45309' },
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
      <circle cx={cx} cy={cy} r={r} fill="transparent" stroke="#e7e8e9" strokeWidth="6" />
      {arcs.map((arc, i) => (
        <circle
          key={i}
          cx={cx}
          cy={cy}
          r={r}
          fill="transparent"
          stroke={arc.color}
          strokeWidth="6"
          strokeDasharray={`${arc.dash} ${circumference - arc.dash}`}
          strokeDashoffset={-arc.offset}
        />
      ))}
    </svg>
  )
}

export default function DetailDrawer({ theme, onClose }) {
  const drawerRef = useRef(null)

  useEffect(() => {
    if (drawerRef.current) {
      drawerRef.current.style.transform = 'translateX(100%)'
      drawerRef.current.style.opacity = '0'
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (drawerRef.current) {
            drawerRef.current.style.transition =
              'transform 300ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease-out'
            drawerRef.current.style.transform = 'translateX(0)'
            drawerRef.current.style.opacity = '1'
          }
        })
      })
    }
  }, [theme?.id])

  if (!theme) return null

  return (
    <div
      ref={drawerRef}
      className="bg-surface-container-lowest rounded-2xl overflow-hidden shadow-ambient border border-outline-variant/10"
    >
      {/* Header */}
      <div
        className="p-4 md:p-6 text-white relative"
        style={{ background: 'linear-gradient(135deg, #002F59 0%, #00467F 100%)' }}
      >
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-bold font-headline">{theme.name}</h3>
          <div className="flex items-center gap-2">
            <span
              className="text-[10px] font-bold px-2 py-1 rounded"
              style={{ background: SENTIMENT_COLOR[theme.sentiment] }}
            >
              ACTIVE
            </span>
            {onClose && (
              <button onClick={onClose} className="p-1 rounded hover:bg-white/10 transition-colors">
                <span className="material-symbols-outlined text-sm">close</span>
              </button>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16 flex items-center justify-center">
            <DonutChart breakdown={theme.sentimentBreakdown} />
            <span className="absolute text-xs font-bold">{theme.sentimentScore}%</span>
          </div>
          <div>
            <p className="text-xs opacity-70">Sentiment Score</p>
            <p className="text-lg font-bold">{theme.sentimentLabel}</p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 md:p-6 space-y-5">
        {/* AI Summary */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span
              className="material-symbols-outlined text-sm text-secondary"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              auto_awesome
            </span>
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary">
              AI Summary
            </h4>
          </div>
          <p className="text-sm text-on-surface-variant leading-relaxed">{theme.aiSummary}</p>
        </div>

        {/* Frequency */}
        <div className="flex items-center gap-3 bg-surface-container-low rounded-xl p-3">
          <span className="material-symbols-outlined text-outline text-sm">bar_chart</span>
          <span className="text-sm font-semibold text-on-surface">
            Mentioned in{' '}
            <span className="text-primary font-bold">{theme.percentage}%</span> of responses
          </span>
        </div>

        {/* Sentiment breakdown bar */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2">
            Sentiment Distribution
          </h4>
          <div className="flex rounded-full overflow-hidden h-2 gap-px">
            <div
              className="h-full transition-all duration-500"
              style={{ width: `${theme.sentimentBreakdown.positive}%`, background: '#005119' }}
            />
            <div
              className="h-full transition-all duration-500"
              style={{ width: `${theme.sentimentBreakdown.neutral}%`, background: '#d97706' }}
            />
            <div
              className="h-full transition-all duration-500"
              style={{ width: `${theme.sentimentBreakdown.negative}%`, background: '#ba1a1a' }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-on-surface-variant mt-1">
            <span>Positive {theme.sentimentBreakdown.positive}%</span>
            <span>Neutral {theme.sentimentBreakdown.neutral}%</span>
            <span>Critical {theme.sentimentBreakdown.negative}%</span>
          </div>
        </div>

        {/* Sub-themes */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-2">
            Sub-themes
          </h4>
          <div className="flex flex-wrap gap-2">
            {theme.subthemes.map((st) => (
              <span
                key={st}
                className="px-3 py-1 bg-surface-container rounded-full text-[10px] font-semibold text-on-surface-variant"
              >
                {st}
              </span>
            ))}
          </div>
        </div>

        {/* Quotes */}
        <div className="space-y-3 pt-2 border-t border-outline-variant/10">
          <h4 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
            Example Comments
          </h4>
          {theme.quotes.map((q, i) => (
            <blockquote
              key={i}
              className="bg-surface p-4 rounded-xl border-l-4 border-tertiary-container italic text-xs text-on-surface-variant leading-relaxed"
            >
              {q}
            </blockquote>
          ))}
          <p className="text-[10px] text-on-surface-variant/50 italic">
            * Illustrative examples, not individual student records.
          </p>
        </div>

        {/* Full analysis link */}
        <Link
          to={`/thema/${theme.id}`}
          onClick={() => window.scrollTo(0, 0)}
          className="border border-primary text-primary rounded-xl px-4 py-2 text-sm font-semibold w-full text-center block hover:bg-primary hover:text-white transition-colors"
        >
          View full analysis →
        </Link>
      </div>
    </div>
  )
}
