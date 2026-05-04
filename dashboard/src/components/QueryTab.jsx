import { useState, useEffect } from 'react';
import { useVectorDB } from '../context/VectorDBContext';

export default function QueryTab() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { refresh } = useVectorDB();

  // Load from localStorage on mount
  useEffect(() => {
    const cached = localStorage.getItem('queryResults');
    const cachedQuery = localStorage.getItem('lastQuery');
    
    if (cached && cachedQuery) {
      try {
        setResults(JSON.parse(cached));
        setQuery(cachedQuery);
      } catch (e) {
        console.error('Failed to load cache:', e);
      }
    }
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 10 })
      });
      
      const data = await response.json();
      
      if (data.error) {
        setError(data.error);
        setResults([]);
      } else {
        const newResults = data.results || [];
        setResults(newResults);
        
        // Cache to localStorage (persists across tabs/refresh)
        localStorage.setItem('queryResults', JSON.stringify(newResults));
        localStorage.setItem('lastQuery', query);
        
        // Refresh overview data
        refresh();
      }
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const clearCache = () => {
    localStorage.removeItem('queryResults');
    localStorage.removeItem('lastQuery');
    setResults([]);
    setQuery('');
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Query Vector Database</h2>
        {results.length > 0 && (
          <button
            onClick={clearCache}
            className="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            Clear Cache
          </button>
        )}
      </div>
      
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Ask a question about the survey data..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="px-4 py-2 bg-green-600 text-white rounded font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-green-700"
        >
          {loading ? '🔍 Searching...' : '🔍 Search'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-100 text-red-800 rounded">
          ❌ {error}
        </div>
      )}

      <div className="space-y-3">
        {results.map((result) => (
          <div 
            key={result.id} 
            className="p-4 bg-gradient-to-r from-gray-50 to-green-50 rounded border-l-4 border-green-500"
          >
            <div className="flex justify-between items-start mb-2">
              <span className="text-sm font-semibold text-gray-700">Result #{result.id}</span>
              <span className="text-sm font-bold bg-green-200 text-green-800 px-3 py-1 rounded">
                {result.percentage}% Match
              </span>
            </div>
            <p className="text-gray-800">{result.preview}</p>
          </div>
        ))}
      </div>
    </div>
  );
}