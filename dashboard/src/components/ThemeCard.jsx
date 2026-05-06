import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function ThemeCard({ theme, isActive, onClick, size }) {
  const activeCls = isActive
    ? 'ring-2 ring-primary scale-[1.02] shadow-ambient bg-blue-50/50'
    : 'hover:scale-[1.02] hover:shadow-ambient bg-white'

  const transition = { type: 'spring', stiffness: 300, damping: 30 }

  if (size === 'large') {
    return (
      <motion.div
        layout
        layoutId={theme.id}
        transition={transition}
        onClick={onClick}
        className={`col-span-2 md:row-span-2 rounded-xl p-4 md:p-6 flex flex-col justify-between cursor-pointer ${activeCls} border border-gray-200 min-h-[160px]`}
      >
        <div className="flex justify-between items-start">
          <span
            className="material-symbols-outlined text-2xl md:text-3xl text-primary"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            {theme.icon}
          </span>
          <span className="text-xs font-bold px-2 py-1 rounded bg-blue-100 text-blue-800">
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
            state={{ theme }}
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
        className={`col-span-2 rounded-xl p-4 md:p-5 flex flex-col justify-between cursor-pointer ${activeCls} border border-gray-200 min-h-[120px]`}
      >
        <div className="flex justify-between items-start">
          <span className="material-symbols-outlined text-2xl text-primary">{theme.icon}</span>
          <span className="text-xs font-bold text-blue-800 bg-blue-100 px-2 rounded">{theme.percentage}%</span>
        </div>
        <h3 className="text-base md:text-lg font-bold font-headline text-primary mt-2">{theme.name}</h3>
        <Link
          to={`/thema/${theme.id}`}
          state={{ theme }}
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
      className={`rounded-xl p-3 md:p-4 flex flex-col justify-between cursor-pointer ${activeCls} border border-gray-200 min-h-[110px]`}
    >
      <div className="flex justify-between items-start">
        <span className="material-symbols-outlined text-xl text-primary">{theme.icon}</span>
        <span className="text-xs font-bold text-blue-800 bg-blue-100 px-1.5 rounded">{theme.percentage}%</span>
      </div>
      <h3 className="text-sm font-bold font-headline text-primary leading-tight mt-2">
        {theme.name}
      </h3>
      {theme.subtag && (
        <p className="text-[10px] text-on-surface-variant mt-1">{theme.subtag}</p>
      )}
      <Link
        to={`/thema/${theme.id}`}
        state={{ theme }}
        onClick={(e) => { e.stopPropagation(); window.scrollTo(0, 0) }}
        className="text-[10px] font-semibold text-primary/70 hover:text-primary mt-1 inline-block"
      >
        View more →
      </Link>
    </motion.div>
  )
}
