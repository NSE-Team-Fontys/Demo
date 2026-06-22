// Module-level cache for stable API responses that don't change until the
// vector DB is rebuilt. Stores the Promise so concurrent callers share the
// same in-flight request instead of firing duplicates.
const _cache = new Map();

export function cachedFetch(url) {
  if (!_cache.has(url)) {
    const promise = fetch(url)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .catch(err => {
        _cache.delete(url); // allow retry on next call if request failed
        throw err;
      });
    _cache.set(url, promise);
  }
  return _cache.get(url);
}

export function invalidateStableCache() {
  _cache.clear();
}
