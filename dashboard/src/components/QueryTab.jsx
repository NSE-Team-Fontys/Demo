import { useState } from 'react';

export default function QueryTab() {
  const [query, setQuery] = useState('');
  const [institution, setInstitution] = useState('all');
  const [numResults, setNumResults] = useState(10);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchPerformed, setSearchPerformed] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const params = new URLSearchParams({
        query: query.trim(),
        n: numResults.toString(),
        ...(institution !== 'all' && { institution })
      });

      const response = await fetch(`http://localhost:5000/api/query-vectors?${params}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (data.status === 'success') {
        setResults(data.results || []);
        setSearchPerformed(true);
      } else {
        setError(data.error || 'Search failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">✨ Query Vector Database</h2>
        <p className="text-gray-600 mt-1">Ask natural language questions about your anonymized feedback</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="bg-gray-50 p-4 rounded-lg space-y-4 border border-gray-200">
          
          {/* Query Input */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Your Question</label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What do students say about the teaching quality?"
              disabled={loading}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none disabled:opacity-50"
              rows="3"
            />
          </div>

          {/* Filters */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Institution</label>
              <select
                value={institution}
                onChange={(e) => setInstitution(e.target.value)}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              >
                <option value="all">All Institutions</option>
                <option value="1">Institution 1</option>
                <option value="2">Institution 2</option>
                <option value="3">Institution 3</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Results</label>
              <input
                type="number"
                min="1"
                max="50"
                value={numResults}
                onChange={(e) => setNumResults(Math.max(1, parseInt(e.target.value) || 10))}
                disabled={loading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold rounded-lg transition flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="animate-spin">⏳</span>
                Searching...
              </>
            ) : (
              <>
                <span>🔍</span>
                Search Database
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <strong>❌ Error:</strong> {error}
        </div>
      )}

      {/* Results */}
      {searchPerformed && !loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-gray-800">
              📊 Results for "{query}"
            </h3>
            <span className="text-sm text-gray-600">
              {institution !== 'all' ? `[${institution}]` : '[All institutions]'} • {results.length} found
            </span>
          </div>

          {results.length === 0 ? (
            <div className="p-6 text-center bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-gray-600">No results found. Try a different query.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((result, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-blue-50 border border-blue-200 rounded-lg hover:shadow-md transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-bold text-blue-700">#{idx + 1}</span>
                    <div className="flex gap-2 text-xs">
                      {result.metadata?.institution && (
                        <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded">
                          {result.metadata.institution}
                        </span>
                      )}
                      {result.similarity !== undefined && (
                        <span className="px-2 py-1 bg-green-200 text-green-800 rounded">
                          Match: {(result.similarity * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-gray-700 leading-relaxed">{result.document}</p>
                  {result.metadata && Object.keys(result.metadata).length > 0 && (
                    <div className="mt-3 text-xs text-gray-600 space-y-1">
                      {Object.entries(result.metadata).map(([key, val]) => (
                        <div key={key}>
                          <strong>{key}:</strong> {val}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}