import { useState } from 'react'
import { PROGRAMMES, COMPARISON_DATA, COMPARISON_LABELS } from '../data/themes'
import { useApiData } from '../hooks/useApiData'

const THEME_KEYS = Object.keys(COMPARISON_LABELS)

function MirroredRow({ label, valueA, valueB, maxVal = 5 }) {
  const pctA = (valueA / maxVal) * 100
  const pctB = (valueB / maxVal) * 100
  const diff = Math.abs(valueA - valueB)
  const significant = diff >= 0.4

  return (
    <div className="grid grid-cols-11 items-center gap-1">
      {/* Left bar (A) */}
      <div className="col-span-5 flex justify-end">
        <div className="w-full bg-surface-container-lowest h-9 rounded-l-full overflow-hidden flex justify-end items-center px-4 relative">
          <div
            className="absolute right-0 top-0 bottom-0 transition-all duration-500"
            style={{ width: `${pctA}%`, background: 'rgba(0,47,89,0.18)' }}
          />
          <span className="relative z-10 text-sm font-bold text-primary">{valueA.toFixed(1)}</span>
        </div>
      </div>

      {/* Centre label */}
      <div className="col-span-1 text-center">
        <span
          className={`text-[9px] font-bold uppercase leading-none block ${
            significant ? 'text-primary' : 'text-on-surface-variant/50'
          }`}
        >
          {label}
        </span>
        {significant && (
          <span className="text-[8px] font-bold text-error block mt-0.5">
            Δ{diff.toFixed(1)}
          </span>
        )}
      </div>

      {/* Right bar (B) */}
      <div className="col-span-5">
        <div className="w-full bg-surface-container-lowest h-9 rounded-r-full overflow-hidden flex justify-start items-center px-4 relative">
          <div
            className="absolute left-0 top-0 bottom-0 transition-all duration-500"
            style={{ width: `${pctB}%`, background: 'rgba(0,106,106,0.18)' }}
          />
          <span className="relative z-10 text-sm font-bold text-secondary">{valueB.toFixed(1)}</span>
        </div>
      </div>
    </div>
  )
}

// ── Live sentiment bar ────────────────────────────────────────────────────────
function SentimentBar({ avg, label }) {
  // avg_sentiment is -1.0 to 1.0 — convert to 0-100 for display
  const pct = Math.round(((avg + 1) / 2) * 100)
  const color = pct >= 65 ? '#005119' : pct <= 38 ? '#ba1a1a' : '#b45309'
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-on-surface-variant w-28 md:w-40 shrink-0 truncate">{label}</span>
      <div className="flex-1 bg-surface-container rounded-full h-2 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-semibold text-on-surface w-10 text-right">
        {avg >= 0 ? '+' : ''}{avg.toFixed(2)}
      </span>
    </div>
  )
}

// ── Live pipeline section ─────────────────────────────────────────────────────
function LiveCompareSection({ compare }) {
  if (!compare || compare.length === 0) return null

  return (
    <div className="mt-10 bg-surface-container-lowest rounded-2xl p-6 md:p-10 shadow-ambient border border-outline-variant/10">
      <div className="flex items-center gap-2 mb-6">
        <span
          className="material-symbols-outlined text-base text-tertiary-container"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          hub
        </span>
        <h2 className="text-base font-bold font-headline text-primary">
          Live Pipeline — Avg Sentiment by Programme
        </h2>
        <span className="ml-auto text-xs font-medium text-tertiary-container bg-tertiary-container/10 px-2 py-0.5 rounded-full">
          Live
        </span>
      </div>

      <div className="space-y-3">
        {compare.map((row) => (
          <SentimentBar
            key={row.group}
            label={row.group}
            avg={row.avg_sentiment ?? 0}
          />
        ))}
      </div>

      {/* Top themes per programme */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {compare.map((row) => (
          <div key={row.group} className="bg-surface-container-low rounded-xl p-4">
            <p className="text-xs font-bold text-primary mb-2 truncate">{row.group}</p>
            <p className="text-[10px] text-on-surface-variant mb-2 uppercase tracking-wider">Top themes</p>
            <div className="flex flex-wrap gap-1.5">
              {(row.top_themes ?? []).slice(0, 5).map(([theme, count]) => (
                <span
                  key={theme}
                  className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium"
                >
                  {theme} ({count})
                </span>
              ))}
              {(!row.top_themes || row.top_themes.length === 0) && (
                <span className="text-[10px] text-on-surface-variant italic">No data yet</span>
              )}
            </div>
            <p className="text-[10px] text-on-surface-variant/60 mt-2">
              {row.total_responses} response{row.total_responses !== 1 ? 's' : ''}
            </p>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-on-surface-variant/40 mt-4">
        Source: NSE pipeline database · {new Date().toLocaleTimeString()}
      </p>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Vergelijken() {
  const [selA, setSelA] = useState('se')
  const [selB, setSelB] = useState('cs')

  const progA = PROGRAMMES.find((p) => p.id === selA)
  const progB = PROGRAMMES.find((p) => p.id === selB)
  const dataA = COMPARISON_DATA[selA]
  const dataB = COMPARISON_DATA[selB]

  // Fetch live compare data (no filters — show all programmes)
  const { compare, isLive, loading } = useApiData({})

  // Sort rows by largest difference
  const sortedKeys = [...THEME_KEYS].sort(
    (a, b) => Math.abs(dataB[b] - dataA[b]) - Math.abs(dataB[a] - dataA[a])
  )

  const biggestDiffKey = sortedKeys.reduce((best, k) =>
    Math.abs(dataA[k] - dataB[k]) > Math.abs(dataA[best] - dataB[best]) ? k : best
  )

  return (
    <main className="max-w-[1280px] mx-auto">
      <div className="flex flex-col md:flex-row min-h-screen">
        {/* Sidebar */}
        <aside className="w-full md:w-72 md:fixed md:right-0 md:top-16 md:h-[calc(100vh-4rem)] bg-surface-container-lowest/85 glass-panel shadow-editorial flex flex-col p-5 gap-4 order-first md:order-last overflow-y-auto">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-1">Filters</h3>
            <p className="text-xs text-on-surface-variant">Refine your insights</p>
          </div>
          {[
            { icon: 'calendar_today', label: 'Academic Year' },
            { icon: 'location_on', label: 'Location' },
            { icon: 'school', label: 'Programme' },
            { icon: 'history_edu', label: 'Study Mode' },
            { icon: 'group', label: 'Cohort' },
          ].map((f, i) => (
            <button
              key={f.label}
              className={`w-full flex items-center gap-3 p-3 text-sm font-medium rounded-xl transition-colors text-left ${
                i === 0
                  ? 'bg-surface-container-low text-primary'
                  : 'text-on-surface-variant hover:bg-surface-container-low'
              }`}
            >
              <span className="material-symbols-outlined text-lg">{f.icon}</span>
              <span>{f.label}</span>
            </button>
          ))}

          {/* Data source indicator */}
          <div className="mt-auto bg-surface-container-low p-4 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-on-surface-variant uppercase">Data Source</span>
              {loading ? (
                <span className="w-2 h-2 rounded-full bg-outline/50 animate-pulse" />
              ) : isLive ? (
                <span className="flex items-center gap-1 text-[10px] font-bold text-tertiary-container">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary-container animate-pulse" />
                  Live
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[10px] text-on-surface-variant/50">
                  <span className="w-1.5 h-1.5 rounded-full bg-outline/40" />
                  Demo
                </span>
              )}
            </div>
            <p className="text-[10px] text-on-surface-variant leading-relaxed">
              Results are based on the National Student Survey (NSE) results from
              Fontys University of Applied Sciences.
            </p>
          </div>
        </aside>

        {/* Main content */}
        <section className="flex-1 p-5 md:p-12 bg-surface md:mr-72">
          {/* Header */}
          <div className="mb-8 md:mb-16">
            <h1 className="text-2xl md:text-4xl font-extrabold tracking-tight font-headline text-primary mb-2">
              Comparative Analysis
            </h1>
            <p className="text-on-surface-variant max-w-2xl font-body">
              Direct comparison of student satisfaction between two programmes based on the
              key NSE themes.
            </p>
          </div>

          {/* Comparison selector */}
          <div className="grid grid-cols-1 md:grid-cols-11 gap-3 md:gap-4 mb-8 md:mb-12 items-center">
            <div className="md:col-span-5 bg-surface-container-lowest p-5 rounded-xl shadow-editorial">
              <label className="text-[10px] uppercase font-bold text-secondary mb-2 block">
                Selection A
              </label>
              <select
                value={selA}
                onChange={(e) => setSelA(e.target.value)}
                className="w-full text-lg font-bold text-primary bg-transparent border-none outline-none cursor-pointer font-headline appearance-none"
              >
                {PROGRAMMES.map((p) => (
                  <option key={p.id} value={p.id} disabled={p.id === selB}>
                    {p.name}
                  </option>
                ))}
              </select>
              <p className="text-sm text-on-surface-variant mt-1">{progA?.year}</p>
            </div>

            <div className="md:col-span-1 flex justify-center">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm text-white"
                style={{ background: 'linear-gradient(135deg, #002F59, #00467F)' }}
              >
                VS
              </div>
            </div>

            <div className="md:col-span-5 md:text-right bg-surface-container-lowest p-5 rounded-xl shadow-editorial">
              <label className="text-[10px] uppercase font-bold text-secondary mb-2 block">
                Selection B
              </label>
              <select
                value={selB}
                onChange={(e) => setSelB(e.target.value)}
                className="w-full text-lg font-bold text-secondary bg-transparent border-none outline-none cursor-pointer font-headline appearance-none text-right"
              >
                {PROGRAMMES.map((p) => (
                  <option key={p.id} value={p.id} disabled={p.id === selA}>
                    {p.name}
                  </option>
                ))}
              </select>
              <p className="text-sm text-on-surface-variant mt-1">{progB?.year}</p>
            </div>
          </div>

          {/* Mirrored mock chart */}
          <div className="bg-surface-container-low rounded-2xl p-4 md:p-10">
            <div className="flex justify-between items-center mb-8 border-b border-outline-variant/10 pb-5">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Satisfaction Score (1–5)
                </span>
              </div>
              <span className="text-sm font-headline font-bold text-primary">Top NSE Themes</span>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Satisfaction Score (1–5)
                </span>
                <span className="w-3 h-3 rounded-full bg-secondary" />
              </div>
            </div>

            <div className="space-y-4">
              {sortedKeys.map((key) => (
                <MirroredRow
                  key={key}
                  label={COMPARISON_LABELS[key]}
                  valueA={dataA[key]}
                  valueB={dataB[key]}
                />
              ))}
            </div>

            <div className="mt-8 flex justify-between text-[10px] font-medium text-on-surface-variant/50 uppercase tracking-widest border-t border-outline-variant/10 pt-4">
              <span>n={progA?.respondents} respondents</span>
              <span>Demo data</span>
              <span>n={progB?.respondents} respondents</span>
            </div>
          </div>

          {/* Analysis cards */}
          <div className="mt-8 md:mt-10 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
            <div className="bg-surface-container-lowest p-8 rounded-2xl shadow-editorial">
              <div className="flex items-center gap-3 mb-4">
                <span className="material-symbols-outlined text-tertiary-container">trending_up</span>
                <h3 className="font-headline font-bold text-lg text-primary">Biggest Difference</h3>
              </div>
              <p className="text-sm text-on-surface-variant leading-relaxed mb-4">
                The most significant difference is visible in{' '}
                <strong>{COMPARISON_LABELS[biggestDiffKey]}</strong>. {progA?.name} scores{' '}
                <strong>{dataA[biggestDiffKey].toFixed(1)}</strong> versus{' '}
                <strong>{dataB[biggestDiffKey].toFixed(1)}</strong> for {progB?.name}.
              </p>
              <div className="flex items-center gap-2 text-xs font-bold text-primary cursor-pointer hover:underline">
                <span>VIEW DETAILED REPORT</span>
                <span className="material-symbols-outlined text-xs">arrow_forward</span>
              </div>
            </div>

            <div
              className="p-8 rounded-2xl text-white shadow-ambient relative overflow-hidden"
              style={{ background: 'linear-gradient(135deg, #002F59 0%, #00467F 100%)' }}
            >
              <div className="relative z-10">
                <h3 className="font-headline font-bold text-lg mb-3">Action Point</h3>
                <p className="text-sm text-blue-100/80 leading-relaxed mb-5">
                  Both programmes score relatively low on{' '}
                  <strong>Guidance</strong>. This presents an opportunity for centralised improvement
                  of the mentoring programme within the Fontys ICT institution.
                </p>
                <button className="bg-white text-primary px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wide hover:bg-surface-container-low transition-colors">
                  Share Insight
                </button>
              </div>
              <span
                className="material-symbols-outlined absolute -bottom-4 -right-4 text-9xl text-white/5"
                style={{ fontSize: '9rem' }}
              >
                lightbulb
              </span>
            </div>
          </div>

          {/* ── Live pipeline section (below mock chart) ── */}
          {isLive && <LiveCompareSection compare={compare} />}

          <footer className="mt-16 text-center text-xs text-on-surface-variant opacity-40">
            © 2025 Fontys University of Applied Sciences - NSE Insights Dashboard. All rights reserved.
          </footer>
        </section>
      </div>
    </main>
  )
}
