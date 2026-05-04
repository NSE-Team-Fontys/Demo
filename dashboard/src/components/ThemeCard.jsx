import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

const SENTIMENT_STYLES = {
  positive: {
    bg: 'bg-tertiary-container/20',
    border: 'border-tertiary-container/30',
    badge: 'bg-tertiary-container text-white',
    icon: 'text-tertiary-container',
  },
  neutral: {
    bg: 'bg-orange-50',
    border: 'border-orange-200/40',
    badge: 'bg-orange-200 text-orange-900',
    icon: 'text-orange-500',
  },
  critical: {
    bg: 'bg-error-container/20',
    border: 'border-error/20',
    badge: 'bg-error-container text-on-error-container',
    icon: 'text-error',
  },
}

export default function ThemeCard({ theme, isActive, onClick, size }) {
  const styles = SENTIMENT_STYLES[theme.sentiment]

  const activeCls = isActive
    ? 'ring-2 ring-primary scale-[1.02] shadow-ambient'
    : 'hover:scale-[1.02] hover:shadow-ambient'

  const transition = { type: 'spring', stiffness: 300, damping: 30 }

  if (size === 'large') {
    return (
      <motion.div
        layout
        layoutId={theme.id}
        transition={transition}
        onClick={onClick}
        className={`col-span-2 md:row-span-2 ${styles.bg} rounded-xl p-4 md:p-6 flex flex-col justify-between cursor-pointer ${activeCls} border ${styles.border} min-h-[160px]`}
      >
        <div className="flex justify-between items-start">
          <span
            className={`material-symbols-outlined text-2xl md:text-3xl ${styles.icon}`}
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            {theme.icon}
          </span>
          <span className={`text-xs font-bold px-2 py-1 rounded ${styles.badge}`}>
            {theme.percentage}%
          </span>
        </div>
        <div>
          <h3 className="text-xl md:text-2xl font-bold font-headline text-primary">{theme.name}</h3>
          {theme.subtag && (
            <p className="text-sm text-on-surface-variant mt-1">{theme.subtag}</p>
          )}
          <Link
            to={`/thema/${theme.id}`}
            onClick={(e) => { e.stopPropagation(); window.scrollTo(0, 0) }}
            className="text-xs font-semibold text-primary/70 hover:text-primary mt-2 inline-block"
          >
            View more →
          </Link>
        </div>
      </motion.div>
    )
  }

  if (size === 'medium') {
    return (
      <motion.div
        layout
        layoutId={theme.id}
        transition={transition}
        onClick={onClick}
        className={`col-span-2 ${styles.bg} rounded-xl p-4 md:p-5 flex flex-col justify-between cursor-pointer ${activeCls} border ${styles.border} min-h-[120px]`}
      >
        <div className="flex justify-between items-start">
          <span className={`material-symbols-outlined text-2xl ${styles.icon}`}>{theme.icon}</span>
          <span className="text-xs font-bold text-on-surface-variant">{theme.percentage}%</span>
        </div>
        <h3 className="text-base md:text-lg font-bold font-headline text-primary mt-2">{theme.name}</h3>
        <Link
          to={`/thema/${theme.id}`}
          onClick={(e) => { e.stopPropagation(); window.scrollTo(0, 0) }}
          className="text-xs font-semibold text-primary/70 hover:text-primary mt-1 inline-block"
        >
          View more →
        </Link>
      </motion.div>
    )
  }

  // small
  return (
    <motion.div
      layout
      layoutId={theme.id}
      transition={transition}
      onClick={onClick}
      className={`${styles.bg} rounded-xl p-3 md:p-4 flex flex-col justify-between cursor-pointer ${activeCls} border ${styles.border} min-h-[110px]`}
    >
      <div className="flex justify-between items-start">
        <span className={`material-symbols-outlined text-xl ${styles.icon}`}>{theme.icon}</span>
        <span className="text-xs font-bold text-on-surface-variant">{theme.percentage}%</span>
      </div>
      <h3 className="text-sm font-bold font-headline text-primary leading-tight mt-2">
        {theme.name}
      </h3>
      {theme.subtag && (
        <p className="text-[10px] text-on-surface-variant mt-1">{theme.subtag}</p>
      )}
      <Link
        to={`/thema/${theme.id}`}
        onClick={(e) => { e.stopPropagation(); window.scrollTo(0, 0) }}
        className="text-[10px] font-semibold text-primary/70 hover:text-primary mt-1 inline-block"
      >
        View more →
      </Link>
    </motion.div>
  )
}
