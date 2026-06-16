/**
 * API service — connects to the NSE pipeline backend at /api/v1.
 * Requests are proxied via Vite: /api → http://localhost:8000
 * All functions return null on failure (network down, API offline, timeout).
 */

import { filtersToLegacyApiParams } from '../utils/filters'

const BASE = '/api/v1'
const TIMEOUT_MS = 5_000

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
  return filtersToLegacyApiParams(filters)
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
