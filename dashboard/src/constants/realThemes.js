export const REAL_THEME_META = {
  'Content and Organisation': {
    id: 'content_org',
    icon: 'menu_book',
    subtag: 'Curriculum and planning',
  },
  'Professional Practice': {
    id: 'link_practice',
    icon: 'work',
    subtag: 'Career readiness',
  },
  Teachers: {
    id: 'teachers',
    icon: 'school',
    subtag: 'Teaching quality',
  },
  'Support / Mentoring': {
    id: 'support',
    icon: 'support_agent',
    subtag: 'Guidance and care',
  },
  'Examination & Assessment': {
    id: 'examination',
    icon: 'gavel',
    subtag: 'Assessment quality',
  },
  'Engagement & Contact': {
    id: 'engagement',
    icon: 'groups',
    subtag: 'Community and belonging',
  },
  'Special Circumstances': {
    id: 'special_circumstances',
    icon: 'accessible',
    subtag: 'Accessibility and accommodations',
  },
}

export const THEME_NAME_BY_ID = Object.fromEntries(
  Object.entries(REAL_THEME_META).map(([name, meta]) => [meta.id, name]),
)

function fallbackId(themeName) {
  return String(themeName || 'theme')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

function sentimentBreakdown(sentiments = []) {
  const total = sentiments.length
  if (!total) return { positive: 0, neutral: 100, negative: 0 }

  const counts = sentiments.reduce(
    (acc, sentiment) => {
      const value = String(sentiment || '').toLowerCase()
      if (value.includes('positive')) acc.positive += 1
      else if (value.includes('negative') || value.includes('critical')) acc.negative += 1
      else acc.neutral += 1
      return acc
    },
    { positive: 0, neutral: 0, negative: 0 },
  )

  return {
    positive: Math.round((counts.positive / total) * 100),
    neutral: Math.round((counts.neutral / total) * 100),
    negative: Math.round((counts.negative / total) * 100),
  }
}

function sentimentFromBreakdown(breakdown) {
  const score = Math.round(breakdown.positive + breakdown.neutral * 0.5)
  if (score >= 65) {
    return { sentimentScore: score, sentiment: 'positive', sentimentLabel: 'Positive' }
  }
  if (score <= 38) {
    return { sentimentScore: score, sentiment: 'critical', sentimentLabel: 'Critical' }
  }
  return { sentimentScore: score, sentiment: 'neutral', sentimentLabel: 'Mixed' }
}

export function buildRealTheme(themeName, insight = {}, { includeInsightDetails = true } = {}) {
  const meta = REAL_THEME_META[themeName] ?? {
    id: fallbackId(themeName),
    icon: 'analytics',
    subtag: null,
  }
  const breakdown = sentimentBreakdown(insight.sentiments)
  const sentiment = sentimentFromBreakdown(breakdown)
  const frequency = typeof insight.frequency === 'number' ? insight.frequency : 0
  const responseCount =
    typeof insight.vector_relevant_count === 'number'
      ? insight.vector_relevant_count
      : typeof insight.document_count === 'number'
        ? insight.document_count
        : 0

  return {
    id: meta.id,
    name: themeName,
    icon: meta.icon,
    size: 'small',
    subtag: meta.subtag,
    percentage: frequency,
    responseCount,
    aiSummary: includeInsightDetails ? insight.summary || '' : '',
    subthemes: includeInsightDetails && Array.isArray(insight.subthemes) ? insight.subthemes : [],
    subtheme_mentions:
      includeInsightDetails && Array.isArray(insight.subtheme_mentions)
        ? insight.subtheme_mentions
        : [],
    quotes: includeInsightDetails && Array.isArray(insight.quotes) ? insight.quotes : [],
    student_suggestions:
      includeInsightDetails && Array.isArray(insight.student_suggestions)
        ? insight.student_suggestions
        : [],
    cachedInsight: includeInsightDetails ? { ...insight, status: 'success' } : null,
    sentimentBreakdown: breakdown,
    ...sentiment,
    trend: [frequency, frequency, frequency, frequency],
    _live: true,
  }
}
