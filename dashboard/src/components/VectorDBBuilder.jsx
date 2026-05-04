import { useState } from 'react';

export default function VectorDBBuilder({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('');

  const handleBuild = async () => {
    setLoading(true);
    setProgress(0);
    setCurrentStage('Initializing...');
    
    try {
      const response = await fetch('http://localhost:5000/api/build-vectors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await response.json();
      setResult(data);
      setProgress(100);
      setCurrentStage('Complete!');
      
      if (data.status === 'success') {
        setTimeout(() => onSuccess?.(), 500);
      }
    } catch (error) {
      setResult({ error: error.message });
      setCurrentStage('Error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">🗄️ Build Vector Database</h2>
      <p className="text-gray-600">Creates embeddings from anonymized data using BAAI/bge-m3</p>

      <button
        onClick={handleBuild}
        disabled={loading}
        className="w-full px-4 py-3 bg-purple-600 text-white rounded font-bold disabled:opacity-50 hover:bg-purple-700 transition"
      >
        {loading ? '⏳ Building vectors...' : '📦 Build Vector DB'}
      </button>

      {loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">Processing embeddings...</span>
            <span className="text-sm font-bold text-purple-600">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div 
              className="bg-purple-600 h-full transition-all duration-500 flex items-center justify-center"
              style={{ width: `${progress}%` }}
            >
              {progress > 10 && (
                <div className="animate-pulse bg-purple-500 h-full w-full"></div>
              )}
            </div>
          </div>
          <div className="flex gap-2 text-sm text-gray-600">
            <span className="animate-spin">⏳</span>
            <span>{currentStage}</span>
          </div>
        </div>
      )}

      {result && (
        <div className={`p-4 rounded font-mono text-sm ${result.error ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
          <strong>{result.status === 'success' ? '✓ Success' : '✗ Error'}</strong>
          <p>{result.message || result.error}</p>
          {result.document_count && <p>📊 Documents indexed: {result.document_count}</p>}
          {result.vectors_created && <p>📈 Vectors created: {result.vectors_created}</p>}
        </div>
      )}
    </div>
  );
}