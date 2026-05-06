import { useMemo } from 'react'
import { Link, NavLink, useLocation, useParams } from 'react-router-dom'
import { getFilteredThemes } from '../data/themes'
import { useThemeSummary } from '../hooks/useThemeSummary'

const BADGE = {
  positive: 'bg-tertiary-container text-white',
  neutral: 'bg-orange-200 text-orange-900',
  critical: 'bg-error-container text-on-error-container',
}

const BADGE_LABEL = {
  positive: 'Positive',
  neutral: 'Neutral',
  critical: 'Critical',
}

function sentimentBadgeClass(sentiment) {
  if (sentiment === 'Positive') return 'bg-green-100 text-green-700'
  if (sentiment === 'Critical') return 'bg-red-100 text-red-700'
  return 'bg-yellow-100 text-yellow-700'
}

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

export default function ViewMorePage() {
  const { id } = useParams()
  const location = useLocation()

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
  const { liveData, loadingLive } = useThemeSummary(theme)

  const comments = liveData?.quotes?.length > 0 ? liveData.quotes : theme?.quotes ?? []
  const subthemes = liveData?.subthemes?.length > 0 ? liveData.subthemes : theme?.subthemes ?? []
  const summary = liveData?.summary || theme?.aiSummary
  const sentiments = liveData?.sentiments ?? []

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
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${BADGE[theme.sentiment]}`}>
                  {BADGE_LABEL[theme.sentiment]}
                </span>
                {loadingLive && (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-white/80">
                    <span className="w-2 h-2 rounded-full bg-white/80 animate-pulse" />
                    Querying VectorDB
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
                  <h2 className="text-sm font-bold text-blue-900">Gemma 4 Live Insights</h2>
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

              {sentiments.length > 0 && (
                <div className="mt-5">
                  <h3 className="text-[10px] font-bold uppercase tracking-wider text-blue-700/70 mb-3">
                    Top Sentiments Detected
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {sentiments.map((sentiment, idx) => (
                      <div key={idx} className="bg-white/70 rounded-xl p-3 border border-blue-100/60 flex gap-3 items-start">
                        <span className={`text-[10px] font-bold px-2 py-1 rounded uppercase mt-0.5 ${sentimentBadgeClass(sentiment.sentiment)}`}>
                          {sentiment.sentiment}
                        </span>
                        <p className="text-sm text-blue-950 leading-snug">{sentiment.point}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
              <div className="flex items-center justify-between gap-3 mb-4">
                <h2 className="text-base md:text-lg font-bold font-headline text-primary">Student Comments</h2>
                <span className="material-symbols-outlined text-outline text-xl">format_quote</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {comments.map((comment, i) => (
                  <blockquote
                    key={i}
                    className="bg-surface p-4 rounded-xl border-l-4 border-blue-500 italic text-sm text-on-surface-variant leading-relaxed shadow-sm"
                  >
                    {comment}
                  </blockquote>
                ))}
              </div>
              <p className="text-[10px] text-on-surface-variant/50 italic mt-4">
                Actual verbatim quotes retrieved from the database when VectorDB is available.
              </p>
            </div>
          </div>

          <aside className="lg:col-span-4 space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
              <StatTile
                icon="bar_chart"
                label="Relevant responses"
                value={`${theme.percentage}%`}
                helper="Share of responses associated with this theme."
              />
              <StatTile
                icon="speed"
                label="Sentiment score"
                value={`${theme.sentimentScore}%`}
                helper={theme.sentimentLabel}
              />
            </div>

            <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
              <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                Sentiment Breakdown
              </h2>
              <div className="flex rounded-full overflow-hidden h-2 gap-px">
                <div className="h-full bg-tertiary-container" style={{ width: `${theme.sentimentBreakdown.positive}%` }} />
                <div className="h-full bg-orange-500" style={{ width: `${theme.sentimentBreakdown.neutral}%` }} />
                <div className="h-full bg-error" style={{ width: `${theme.sentimentBreakdown.negative}%` }} />
              </div>
              <div className="grid grid-cols-3 gap-2 text-[10px] text-on-surface-variant mt-3">
                <span>Positive {theme.sentimentBreakdown.positive}%</span>
                <span className="text-center">Neutral {theme.sentimentBreakdown.neutral}%</span>
                <span className="text-right">Critical {theme.sentimentBreakdown.negative}%</span>
              </div>
            </div>

            <div className="bg-surface-container-lowest rounded-2xl p-4 md:p-6 shadow-ambient border border-outline-variant/10">
              <h2 className="text-xs font-bold uppercase tracking-wider text-on-surface-variant mb-4">
                Key Sub-themes Detected
              </h2>
              <div className="flex flex-wrap gap-2">
                {subthemes.map((subtheme, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 bg-surface-container rounded-full text-xs font-semibold text-on-surface-variant border border-outline/10 shadow-sm"
                  >
                    {subtheme}
                  </span>
                ))}
              </div>
            </div>

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
