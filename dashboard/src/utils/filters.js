import { CITY_TO_BRIN } from '../constants/locations'

export const DEFAULT_FILTERS = {
  jaar: 'All',
  locatie: 'All',
  opleiding: 'All',
  studievorm: 'All',
  cohort: 'All',
  sector: 'All',
  taal: 'All',
}

const FILTER_KEYS = Object.keys(DEFAULT_FILTERS)

function normalizeValue(value) {
  if (value === undefined || value === null || value === '' || value === 'all') return 'All'
  if (value === 'All locations') return 'All'
  return String(value)
}

export function normalizeFilters(filters = {}) {
  return FILTER_KEYS.reduce((acc, key) => {
    acc[key] = normalizeValue(filters[key] ?? DEFAULT_FILTERS[key])
    return acc
  }, {})
}

export function hasActiveFilters(filters = {}) {
  return Object.values(normalizeFilters(filters)).some((value) => value !== 'All')
}

export function filtersFromSearchParams(searchParams) {
  const params = searchParams instanceof URLSearchParams
    ? searchParams
    : new URLSearchParams(searchParams)

  return normalizeFilters(
    FILTER_KEYS.reduce((acc, key) => {
      if (params.has(key)) acc[key] = params.get(key)
      return acc
    }, {}),
  )
}

export function filtersToSearchParams(filters = {}) {
  const normalized = normalizeFilters(filters)
  const params = new URLSearchParams()

  FILTER_KEYS.forEach((key) => {
    if (normalized[key] !== 'All') params.set(key, normalized[key])
  })

  return params
}

export function searchFromFilters(filters = {}) {
  const params = filtersToSearchParams(filters)
  const search = params.toString()
  return search ? `?${search}` : ''
}

export function filtersToApiParams(filters = {}) {
  const normalized = normalizeFilters(filters)
  const params = {
    academic_year: normalized.jaar,
    location: normalized.locatie !== 'All'
      ? CITY_TO_BRIN[normalized.locatie] || normalized.locatie
      : 'All',
    programme: normalized.opleiding,
    study_mode: normalized.studievorm,
    cohort: normalized.cohort,
    sector: normalized.sector,
    language: normalized.taal,
  }

  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value && value !== 'All'),
  )
}

export function stableFilterKey(filters = {}) {
  return JSON.stringify(Object.fromEntries(Object.entries(filters || {}).sort()))
}

export function filtersToLegacyApiParams(filters = {}) {
  const normalized = normalizeFilters(filters)
  const params = {}

  if (normalized.jaar !== 'All') {
    const year = parseInt(normalized.jaar.split('/')[0], 10)
    if (!Number.isNaN(year)) params.year = year
  }
  if (normalized.locatie !== 'All') {
    params.location = CITY_TO_BRIN[normalized.locatie] || normalized.locatie
  }
  if (normalized.opleiding !== 'All') params.programme = normalized.opleiding
  if (normalized.studievorm !== 'All') params.mode = normalized.studievorm.toLowerCase()

  return params
}
