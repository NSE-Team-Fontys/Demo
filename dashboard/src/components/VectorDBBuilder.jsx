import { useState } from 'react';

export default function VectorDBBuilder({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleBuild = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/build-vectors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await response.json();
      setResult(data);
      if (data.status === 'success') {
        setTimeout(() => onSuccess(), 500);
      }
    } catch (error) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Build Vector Database</h2>
      <p className="text-gray-600">Creates embeddings from anonymized data</p>

      <button
        onClick={handleBuild}
        disabled={loading}
        className="w-full px-4 py-3 bg-purple-600 text-white rounded font-bold disabled:opacity-50 hover:bg-purple-700"
      >
        {loading ? '⏳ Building vectors...' : '📦 Build Vector DB'}
      </button>

      {result && (
        <div className={`p-4 rounded font-mono text-sm ${result.error ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
          <strong>{result.status === 'success' ? '✓ Success' : '✗ Error'}</strong>
          <p>{result.message || result.error}</p>
          {result.document_count && <p>Documents indexed: {result.document_count}</p>}
        </div>
      )}
    </div>
  );
}