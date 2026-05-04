/**
 * API service — connects to the NSE pipeline backend at /api/v1.
 * Requests are proxied via Vite: /api → http://localhost:8000
 * All functions return null on failure (network down, API offline, timeout).
 */

const BASE = '/api/v1'
const TIMEOUT_MS = 5_000

// ── Theme ID mapping: API controlled-vocabulary → dashboard theme IDs ─────────
// Keys are the API theme IDs; values are dashboard IDs (null = no static card — card is generated dynamically).
export const API_TO_DASHBOARD = {
  begeleiding:         'begeleiding',
  faciliteiten:        'faciliteiten',
  roostering:          'roosters',
  stage:               'stagebegeleiding',
  onderwijs_kwaliteit: 'leeromgeving',
  studielast:          null,
  communicatie:        null,
  digitalisering:      null,
  inclusiviteit:       null,
  studentenwelzijn:    null,
}

// ── Metadata for dynamically generated theme cards ────────────────────────────
// Used when the API returns a theme that has no static mock card.
const DYNAMIC_THEME_META = {
  studielast: {
    name: 'Workload',
    icon: 'fitness_center',
    subthemes: ['Study pressure', 'Deadlines', 'Work-life balance'],
    aiSummary: 'Students report on the balance between study load and available time. Deadlines and concurrent assignments are recurring themes.',
  },
  communicatie: {
    name: 'Communication',
    icon: 'forum',
    subthemes: ['Information provision', 'Notifications', 'Clarity'],
    aiSummary: 'Communication from the institution is an important factor in student satisfaction. Timeliness and clarity of information are frequently mentioned.',
  },
  digitalisering: {
    name: 'Digitalisation',
    icon: 'devices',
    subthemes: ['Digital tools', 'Online lessons', 'Software'],
    aiSummary: 'Students share experiences with digital tools and online education. Both opportunities and challenges of digitalisation are mentioned.',
  },
  inclusiviteit: {
    name: 'Inclusivity',
    icon: 'diversity_3',
    subthemes: ['Accessibility', 'Diversity', 'Support'],
    aiSummary: 'Students reflect on how inclusive and accessible the education environment is for everyone, regardless of background or circumstance.',
  },
  studentenwelzijn: {
    name: 'Student Wellbeing',
    icon: 'favorite',
    subthemes: ['Mental health', 'Support', 'Social safety'],
    aiSummary: 'Student wellbeing encompasses mental health, social safety and available support. An important indicator for overall student satisfaction.',
  },
}

// ── Internal fetch helper ─────────────────────────────────────────────────────
async function apiFetch(path, params = {}) {
  const url = new URL(BASE + path, window.location.origin)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== null && v !== undefined) url.searchParams.set(k, String(v))
  })
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(url.toString(), { signal: controller.signal })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } finally {
    clearTimeout(timer)
  }
}

// ── Filter conversion: dashboard filters → API query params ──────────────────
export function filtersToParams(filters = {}) {
  const { jaar, locatie, opleiding, studievorm } = filters
  const params = {}

  // "2025/2026" → year=2025
  if (jaar && jaar !== 'All') {
    const y = parseInt(jaar.split('/')[0], 10)
    if (!isNaN(y)) params.year = y
  }
  if (locatie && locatie !== 'All locations') params.location = locatie
  if (opleiding && opleiding !== 'All')        params.programme = opleiding
  if (studievorm && studievorm !== 'All')      params.mode = studievorm.toLowerCase()

  return params
}

// ── Public API ────────────────────────────────────────────────────────────────

/** Returns theme frequency + sentiment stats, or null on failure. */
export async function fetchThemes(filters = {}) {
  try { return await apiFetch('/themes/', filtersToParams(filters)) }
  catch { return null }
}

/** Returns per-group sentiment overview, or null on failure. */
export async function fetchSentiment(filters = {}) {
  try { return await apiFetch('/sentiment/', filtersToParams(filters)) }
  catch { return null }
}

/** Returns comparison data grouped by programme/location/mode, or null on failure. */
export async function fetchCompare(filters = {}, groupBy = 'programme') {
  try {
    return await apiFetch('/compare/', { ...filtersToParams(filters), group_by: groupBy })
  } catch { return null }
}

/** Returns true if the backend is reachable. */
export async function checkHealth() {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 3_000)
    const res = await fetch('/health', { signal: controller.signal })
    clearTimeout(timer)
    return res.ok
  } catch { return false }
}

// ── Data merge helpers ────────────────────────────────────────────────────────

// ── Shared helper: compute sentiment fields from a score ──────────────────────
function sentimentFromScore(score) {
  return {
    sentiment: score >= 65 ? 'positive' : score <= 38 ? 'critical' : 'neutral',
    sentimentLabel:
      score >= 75 ? 'Very Positive' :
      score >= 60 ? 'Positive'      :
      score >= 45 ? 'Mixed'         :
      score >= 30 ? 'Neutral'       : 'Critical',
  }
}

/**
 * Merge live API theme data on top of mock dashboard themes.
 * - Existing mock cards get updated with real counts + sentiment from the API.
 * - API themes without a static mock card are appended as dynamically generated cards.
 */
export function mergeWithLiveData(mockThemes, liveThemes) {
  if (!liveThemes || liveThemes.length === 0) return mockThemes

  // Build lookup: dashboardId → live API row (for existing cards)
  const liveMap = {}
  // Track which API themes have no static card (for dynamic cards)
  const unmapped = []
  let totalResponses = 0

  for (const item of liveThemes) {
    const dashId = API_TO_DASHBOARD[item.theme]
    if (dashId) {
      liveMap[dashId] = item
    } else if (item.theme in API_TO_DASHBOARD) {
      // Mapped to null — needs a dynamic card
      unmapped.push(item)
    }
    totalResponses += item.total ?? 0
  }

  // 1. Update existing mock cards with live data
  const updatedMock = mockThemes.map((theme) => {
    const live = liveMap[theme.id]
    if (!live) return theme

    const score = live.sentiment_score ?? theme.sentimentScore
    const pct   = totalResponses > 0
      ? Math.round((live.total / totalResponses) * 100)
      : theme.percentage

    return {
      ...theme,
      percentage:        pct,
      sentimentScore:    score,
      ...sentimentFromScore(score),
      sentimentBreakdown: {
        positive: live.positive ?? theme.sentimentBreakdown.positive,
        neutral:  live.neutral  ?? theme.sentimentBreakdown.neutral,
        negative: live.negative ?? theme.sentimentBreakdown.negative,
      },
      _live: true,
    }
  })

  // 2. Create dynamic cards for unmapped API themes
  const dynamicCards = unmapped.map((item) => {
    const meta  = DYNAMIC_THEME_META[item.theme] ?? {
      name:       item.theme,
      icon:       'analytics',
      subthemes:  [],
      aiSummary:  '',
    }
    const score = item.sentiment_score ?? 50
    const pct   = totalResponses > 0
      ? Math.round((item.total / totalResponses) * 100)
      : 0

    return {
      id:            item.theme,
      name:          meta.name,
      icon:          meta.icon,
      size:          'small',
      subtag:        null,
      subthemes:     meta.subthemes,
      quotes:        [],
      aiSummary:     meta.aiSummary,
      percentage:    pct,
      sentimentScore: score,
      ...sentimentFromScore(score),
      sentimentBreakdown: {
        positive: item.positive ?? 0,
        neutral:  item.neutral  ?? 0,
        negative: item.negative ?? 0,
      },
      // Flat trend line — no historical data available for live-only themes
      trend:      [pct, pct, pct, pct],
      comparison: { voltijd: score, deeltijd: score, duaal: score },
      _live:    true,
      _dynamic: true,   // flag: this card did not exist in mock data
    }
  })

  return [...updatedMock, ...dynamicCards]
}
