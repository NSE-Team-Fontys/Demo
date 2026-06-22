export const REAL_THEME_META = {
  'Content and Organisation': {
    id: 'content_org',
    icon: 'menu_book',
    subtag: 'Curriculum and planning',
    description: 'Whether the curriculum feels coherent, relevant, manageable, and well organized.',
  },
  'Professional Practice': {
    id: 'link_practice',
    icon: 'work',
    subtag: 'Career readiness',
    description: 'How well the programme prepares students for real professional work.',
  },
  Teachers: {
    id: 'teachers',
    icon: 'school',
    subtag: 'Teaching quality',
    description: 'How students experience teachers, their explanations, and classroom support.',
  },
  'Support / Mentoring': {
    id: 'support',
    icon: 'support_agent',
    subtag: 'Guidance and care',
    description: 'Whether students can find useful guidance when they need support.',
  },
  'Examination & Assessment': {
    id: 'examination',
    icon: 'gavel',
    subtag: 'Assessment quality',
    description: 'Whether assessment, grading, and feedback feel clear, fair, and useful.',
  },
  'Engagement & Contact': {
    id: 'engagement',
    icon: 'groups',
    subtag: 'Community and belonging',
    description: 'Whether students feel connected, motivated, heard, and able to reach teachers.',
  },
  'Special Circumstances': {
    id: 'special_circumstances',
    icon: 'accessible',
    subtag: 'Accessibility and accommodations',
    description: 'How well the programme supports students whose circumstances affect studying.',
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

export function buildRealTheme(themeName, insight = {}, { includeInsightDetails = true } = {}) {
  const meta = REAL_THEME_META[themeName] ?? {
    id: fallbackId(themeName),
    icon: 'analytics',
    subtag: null,
  }
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
    description: meta.description ?? '',
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
    trend: [frequency, frequency, frequency, frequency],
    _live: true,
  }
}
