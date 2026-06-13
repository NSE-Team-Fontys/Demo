import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

function MiniDonutChart({ subthemeMentions }) {
  if (!subthemeMentions || subthemeMentions.length === 0) return null

  const radius = 16
  const strokeWidth = 5
  const circ = 2 * Math.PI * radius // ~100.5

  let currentOffset = 0
  const colors = ['#002F59', '#006A6A', '#3C8D8D', '#727781', '#A9A9A9']

  return (
    <svg width="40" height="40" viewBox="0 0 40 40" className="transform -rotate-90 shrink-0">
      {/* Background circle */}
      <circle
        cx="20"
        cy="20"
        r={radius}
        fill="transparent"
        stroke="#E6E8EE"
        strokeWidth={strokeWidth}
      />
      {subthemeMentions.map((sm, idx) => {
        const pct = sm.percentage || 0
        if (pct <= 0) return null
        const strokeLength = (pct / 100) * circ
        const offset = currentOffset
        currentOffset += strokeLength
        const color = colors[idx % colors.length]

        return (
          <circle
            key={sm.subtheme}
            cx="20"
            cy="20"
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${strokeLength} ${circ}`}
            strokeDashoffset={-offset}
            strokeLinecap="round"
          />
        )
      })}
    </svg>
  )
}

export default function ThemeCard({ theme, size, filters }) {
  const transition = { type: 'spring', stiffness: 300, damping: 30 }
  const subthemeMentions = theme.cachedInsight?.subtheme_mentions || theme.subtheme_mentions || []

  if (size === 'large') {
    return (
      <Link
        to={`/thema/${theme.id}`}
        state={{ theme, filters }}
        onClick={() => window.scrollTo(0, 0)}
        className="block no-underline font-sans"
      >
        <motion.div
          layout
          layoutId={theme.id}
          transition={transition}
          className="rounded-2xl p-5 md:p-6 flex flex-col justify-between hover:scale-[1.02] hover:shadow-ambient bg-white border border-gray-200 min-h-[185px] transition-all duration-300 group shadow-sm"
        >
          <div className="flex justify-between items-start gap-4">
            <div className="flex flex-col gap-2">
              <span
                className="material-symbols-outlined text-3xl text-primary"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                {theme.icon}
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-primary border border-blue-100/50 w-fit">
                {theme.responseCount ?? theme.percentage} comments
              </span>
            </div>
            {/* SVG Pie Chart */}
            <MiniDonutChart subthemeMentions={subthemeMentions} />
          </div>
          <div className="mt-4">
            <h3 className="text-lg md:text-xl font-bold font-headline text-primary group-hover:text-primary-variant transition-colors">
              {theme.name}
            </h3>
            {theme.subtag && (
              <p className="text-xs text-on-surface-variant/80 mt-1">{theme.subtag}</p>
            )}
            
            {/* Key sub-themes pill badges in Overview */}
            {theme.subthemes && theme.subthemes.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {theme.subthemes.slice(0, 3).map((st) => (
                  <span key={st} className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200/50">
                    {st}
                  </span>
                ))}
                {theme.subthemes.length > 3 && (
                  <span className="text-[9px] font-bold text-slate-500 self-center pl-0.5">
                    +{theme.subthemes.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </Link>
    )
  }

  // small card
  return (
    <Link
      to={`/thema/${theme.id}`}
      state={{ theme, filters }}
      onClick={() => window.scrollTo(0, 0)}
      className="block no-underline font-sans"
    >
      <motion.div
        layout
        layoutId={theme.id}
        transition={transition}
        className="rounded-xl p-4 flex flex-col justify-between hover:scale-[1.02] hover:shadow-ambient bg-white border border-gray-200 min-h-[145px] transition-all duration-300 group shadow-sm"
      >
        <div className="flex justify-between items-start gap-2">
          <div className="flex flex-col gap-1.5">
            <span className="material-symbols-outlined text-2xl text-primary">{theme.icon}</span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-50 text-primary border border-blue-100/50 w-fit">
              {theme.responseCount ?? theme.percentage} comments
            </span>
          </div>
          {/* Mini SVG Pie Chart */}
          <MiniDonutChart subthemeMentions={subthemeMentions} />
        </div>
        <div className="mt-3">
          <h3 className="text-sm font-bold font-headline text-primary leading-tight group-hover:text-primary-variant transition-colors">
            {theme.name}
          </h3>
          {theme.subtag && (
            <p className="text-[10px] text-on-surface-variant/70 mt-0.5">{theme.subtag}</p>
          )}

          {/* Key sub-themes list inline in Overview */}
          {theme.subthemes && theme.subthemes.length > 0 && (
            <p className="text-[10px] text-slate-500 mt-2 line-clamp-1 truncate font-medium">
              {theme.subthemes.slice(0, 2).join(', ')}
            </p>
          )}
        </div>
      </motion.div>
    </Link>
  )
}
