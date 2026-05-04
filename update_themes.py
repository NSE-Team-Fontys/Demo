import json

content = '''// Mock NSE theme data

export const YEARS = ['22/23', '23/24', '24/25', '25/26']

export const FILTER_OPTIONS = {
  jaar: ['2022/2023', '2023/2024', '2024/2025', '2025/2026'],
  locatie: ['All locations', 'Eindhoven', 'Tilburg', 'Den Bosch', 'Venlo'],
  opleiding: [
    'Software Engineering',
    'Cyber Security',
    'Artificial Intelligence',
    'ICT & Business',
    'HBO-ICT',
  ],
  studievorm: ['All', 'Full-time', 'Part-time', 'Dual'],
  cohort: ['All', '2022', '2023', '2024', '2025'],
}

const BASE_THEMES = [
  {
    id: 'content_org',
    name: 'Content and Organisation',
    icon: 'menu_book',
    size: 'large',
    subtag: 'Core Curriculum',
    subthemes: ['Relevance', 'Study materials', 'Challenge level'],
    quotes: [
      '"The curriculum structure is well thought out, but the materials could be more up-to-date."',
      '"The academic workload pressure is high but manageable."'
    ],
    aiSummary: 'Students find the curriculum coherent but report varied experiences regarding the academic workload pressure.'
  },
  {
    id: 'link_practice',
    name: 'Professional Practice',
    icon: 'work',
    size: 'medium',
    subtag: 'Career Readiness',
    subthemes: ['Internships', 'Guest speakers', 'Skill acquisition'],
    quotes: [
      '"The guest lectures from industry professionals really bridge the gap between theory and practice."',
      '"More opportunities to connect with external companies would be appreciated."'
    ],
    aiSummary: 'Strong appreciation for internships and industry connections, highlighting a solid preparation for the working world.'
  },
  {
    id: 'teachers',
    name: 'Teachers',
    icon: 'school',
    size: 'medium',
    subtag: 'Teaching Quality',
    subthemes: ['Subject expertise', 'Didactic skill', 'Support'],
    quotes: [
      '"Lecturers are very knowledgeable and inspire confidence in the subject matter."',
      '"The psychological safety in the classroom allows for open discussions."'
    ],
    aiSummary: 'Teachers are generally praised for their subject expertise and creating a safe, inspiring classroom environment.'
  },
  {
    id: 'support',
    name: 'Support / Mentoring',
    icon: 'psychology',
    size: 'small',
    subtag: 'Non-academic guidance',
    subthemes: ['Mentors', 'Student advisors', 'Career counsellors'],
    quotes: [
      '"The student advisors are easily reachable and provide great non-academic guidance."',
      '"Mentoring availability could be improved during exam periods."'
    ],
    aiSummary: 'Support staff are valued for their guidance, though availability during peak times is a recurring concern.'
  },
  {
    id: 'examination',
    name: 'Examination & Assessment',
    icon: 'gavel',
    size: 'small',
    subtag: 'Assessment Quality',
    subthemes: ['Grading criteria', 'Feedback usefulness', 'Alignment'],
    quotes: [
      '"The grading criteria are transparent, but the feedback received could be more detailed."',
      '"Assessments align well with the course content taught."'
    ],
    aiSummary: 'Assessments are seen as well-aligned with coursework, but students desire more constructive feedback.'
  },
  {
    id: 'engagement',
    name: 'Engagement & Contact',
    icon: 'groups',
    size: 'small',
    subtag: 'Student Involvement',
    subthemes: ['Belonging', 'Teacher accessibility', 'Feedback valued'],
    quotes: [
      '"I feel a strong sense of belonging and my feedback seems genuinely valued."',
      '"Teacher accessibility makes it easy to stay engaged with the materials."'
    ],
    aiSummary: 'A positive sense of belonging and active engagement with materials are frequently reported.'
  },
  {
    id: 'special_circumstances',
    name: 'Special Circumstances',
    icon: 'accessible',
    size: 'large',
    subtag: 'Accommodations',
    subthemes: ['Disability', 'Financial stress', 'Caregiving'],
    quotes: [
      '"The institution was very accommodating regarding my special circumstances."',
      '"Digital resources are highly accessible, which helps immensely."'
    ],
    aiSummary: 'The institution handles special circumstances well, providing satisfactory accommodations and accessible resources.'
  }
]

const AI_SUMMARIES = {}
const QUOTES = {}

export const OPLEIDING_PROFILES = {
  'Software Engineering': {
    content_org: { percentage: 20, sentiment: 'positive', sentimentScore: 75, sentimentBreakdown: { positive: 75, neutral: 15, negative: 10 }, trend: [15, 18, 19, 20], comparison: { voltijd: 80, deeltijd: 65, duaal: 50 } },
    link_practice: { percentage: 15, sentiment: 'positive', sentimentScore: 70, sentimentBreakdown: { positive: 70, neutral: 20, negative: 10 }, trend: [12, 14, 15, 15], comparison: { voltijd: 75, deeltijd: 60, duaal: 65 } },
    teachers: { percentage: 15, sentiment: 'neutral', sentimentScore: 60, sentimentBreakdown: { positive: 60, neutral: 25, negative: 15 }, trend: [14, 14, 15, 15], comparison: { voltijd: 65, deeltijd: 55, duaal: 50 } },
    support: { percentage: 10, sentiment: 'neutral', sentimentScore: 55, sentimentBreakdown: { positive: 55, neutral: 30, negative: 15 }, trend: [8, 9, 10, 10], comparison: { voltijd: 60, deeltijd: 50, duaal: 55 } },
    examination: { percentage: 15, sentiment: 'critical', sentimentScore: 40, sentimentBreakdown: { positive: 40, neutral: 30, negative: 30 }, trend: [12, 13, 14, 15], comparison: { voltijd: 45, deeltijd: 35, duaal: 40 } },
    engagement: { percentage: 15, sentiment: 'positive', sentimentScore: 65, sentimentBreakdown: { positive: 65, neutral: 25, negative: 10 }, trend: [10, 12, 14, 15], comparison: { voltijd: 70, deeltijd: 60, duaal: 55 } },
    special_circumstances: { percentage: 10, sentiment: 'neutral', sentimentScore: 50, sentimentBreakdown: { positive: 50, neutral: 35, negative: 15 }, trend: [8, 9, 9, 10], comparison: { voltijd: 55, deeltijd: 45, duaal: 40 } }
  }
}

// Mirror SE profile for others to keep it simple
const defaultProfile = OPLEIDING_PROFILES['Software Engineering']
for (const p of ['Cyber Security', 'Artificial Intelligence', 'ICT & Business', 'HBO-ICT']) {
  OPLEIDING_PROFILES[p] = JSON.parse(JSON.stringify(defaultProfile))
}

const STUDIEVORM_MODIFIERS = { 'All': {}, 'Full-time': {}, 'Part-time': {}, 'Dual': {} }
const LOCATIE_MODIFIERS = { 'All locations': {}, 'Eindhoven': {}, 'Tilburg': {}, 'Den Bosch': {}, 'Venlo': {} }
const JAAR_MODIFIERS = { '2022/2023': {}, '2023/2024': {}, '2024/2025': {}, '2025/2026': {} }
const COHORT_MODIFIERS = { 'All': {}, '2022': {}, '2023': {}, '2024': {}, '2025': {} }

function clamp(v, min = 0, max = 100) { return Math.max(min, Math.min(max, v)) }

function applyModifiers(stats, ...modSets) {
  let s  = { ...stats }
  let bd = { ...stats.sentimentBreakdown }
  for (const mods of modSets) {
    if (!mods) continue
    if (mods.scoreDelta)      s.sentimentScore = clamp(s.sentimentScore + mods.scoreDelta)
    if (mods.positiveDelta)   bd.positive      = clamp(bd.positive + mods.positiveDelta)
    if (mods.negativeDelta)   bd.negative      = clamp(bd.negative + mods.negativeDelta)
    if (mods.percentageDelta) s.percentage     = clamp(s.percentage + mods.percentageDelta, 1, 35)
  }
  bd.neutral = clamp(100 - bd.positive - bd.negative)
  if (s.sentimentScore >= 65)      s.sentiment = 'positive'
  else if (s.sentimentScore <= 38) s.sentiment = 'critical'
  else                             s.sentiment = 'neutral'
  s.sentimentLabel =
    s.sentimentScore >= 75 ? 'Very Positive' :
    s.sentimentScore >= 60 ? 'Positive' :
    s.sentimentScore >= 45 ? 'Mixed' :
    s.sentimentScore >= 30 ? 'Neutral' : 'Critical'
  s.sentimentBreakdown = bd
  return s
}

export function getFilteredThemes(filters) {
  const { opleiding, studievorm, locatie, jaar, cohort } = filters
  const profile    = OPLEIDING_PROFILES[opleiding] || OPLEIDING_PROFILES['Software Engineering']
  const svMods     = STUDIEVORM_MODIFIERS[studievorm] || {}
  const locMods    = LOCATIE_MODIFIERS[locatie]       || {}
  const jaarMods   = JAAR_MODIFIERS[jaar]             || {}
  const cohortMods = COHORT_MODIFIERS[cohort]         || {}

  return BASE_THEMES.map((base) => {
    const profileData = profile[base.id] || profile['content_org']
    const merged = applyModifiers(
      profileData,
      svMods[base.id],
      locMods[base.id],
      jaarMods[base.id],
      cohortMods[base.id],
    )
    const aiSummary = AI_SUMMARIES[base.id]?.[opleiding] ?? AI_SUMMARIES[base.id]?.default ?? base.aiSummary
    const quotes    = QUOTES[base.id]?.[opleiding]       ?? QUOTES[base.id]?.default       ?? base.quotes
    return { ...base, ...merged, aiSummary, quotes }
  })
}

export const THEMES = getFilteredThemes({
  opleiding:  'Software Engineering',
  studievorm: 'All',
  locatie:    'All locations',
  jaar:       '2025/2026',
  cohort:     'All',
})

export const PROGRAMMES = [
  { id: 'se',  name: 'Software Engineering',   year: '2024/2025', respondents: 432 },
  { id: 'cs',  name: 'Cyber Security',          year: '2024/2025', respondents: 287 },
  { id: 'ai',  name: 'Artificial Intelligence', year: '2024/2025', respondents: 198 },
  { id: 'ict', name: 'ICT & Business',           year: '2024/2025', respondents: 311 },
]

export const COMPARISON_DATA = {
  se:  { inhoud: 4.4, docenten: 3.8, sfeer: 4.6, begeleiding: 3.2, toetsing: 4.0, faciliteiten: 3.7, beroep: 4.5, planning: 3.6, betrokken: 4.2, studielast: 3.9 },
  cs:  { inhoud: 4.1, docenten: 4.3, sfeer: 4.2, begeleiding: 3.5, toetsing: 3.9, faciliteiten: 4.1, beroep: 4.4, planning: 3.3, betrokken: 3.9, studielast: 3.7 },
  ai:  { inhoud: 4.6, docenten: 4.1, sfeer: 4.0, begeleiding: 3.8, toetsing: 3.7, faciliteiten: 3.5, beroep: 4.7, planning: 3.4, betrokken: 4.4, studielast: 4.1 },
  ict: { inhoud: 4.2, docenten: 3.9, sfeer: 4.3, begeleiding: 3.6, toetsing: 3.8, faciliteiten: 4.0, beroep: 4.1, planning: 3.7, betrokken: 4.0, studielast: 3.8 },
}

export const COMPARISON_LABELS = {
  inhoud: 'Content', docenten: 'Lecturers', sfeer: 'Atmosphere', begeleiding: 'Guidance',
  toetsing: 'Assessment', faciliteiten: 'Facilities', beroep: 'Career',
  planning: 'Planning', betrokken: 'Engagement', studielast: 'Workload',
}
'''
with open('dashboard/src/data/themes.js', 'w', encoding='utf-8') as f:
    f.write(content)
