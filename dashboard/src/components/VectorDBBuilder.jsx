import { useState, useRef } from 'react';

export default function VectorDBBuilder({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('');
  const [currentDoc, setCurrentDoc] = useState('');

  const handleBuild = async () => {
    setLoading(true);
    setProgress(0);
    setCurrentStage('Initializing Connection...');
    setCurrentDoc('');
    setResult(null);
    
    try {
      const response = await fetch('http://localhost:5000/api/build-vectors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      
      if (!response.body) throw new Error("ReadableStream not yet supported in this browser.");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line.trim());
                if (data.status === 'progress') {
                  if (data.progress !== undefined) setProgress(data.progress);
                  if (data.message) setCurrentStage(data.message);
                  if (data.current_doc) setCurrentDoc(data.current_doc);
                } else if (data.status === 'success') {
                  setResult(data);
                  setProgress(100);
                  setCurrentStage('Embeddings Generated and Indexed!');
                  setTimeout(() => onSuccess?.(), 2000);
                } else if (data.status === 'error') {
                  setResult({ error: data.error });
                  break;
                }
              } catch (e) {
                console.error("Failed to parse line", line);
              }
            }
          }
        }
      }
    } catch (error) {
      setResult({ error: error.message });
      setCurrentStage('Error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6 bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-100 transition-all duration-500">
      <div className="flex items-center space-x-4 pb-4 border-b border-gray-100">
        <div className="p-3 bg-gradient-to-tr from-fuchsia-500 to-rose-500 text-white rounded-xl shadow-lg">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900">Semantic Vector Database</h2>
          <p className="text-gray-500 text-sm mt-1">Convert text answers into high-dimensional semantic vectors using BAAI/bge-m3</p>
        </div>
      </div>

      {!loading && !result && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 text-center py-8 px-4">
          <div className="bg-fuchsia-50 p-6 rounded-3xl border border-fuchsia-100 inline-block mb-6 shadow-sm">
            <svg className="w-16 h-16 text-fuchsia-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">Ready to Build the Knowledge Base</h3>
          <p className="text-gray-500 max-w-lg mx-auto mb-8 text-sm">
            This will take the anonymized survey records, encode them into high-dimensional vectors, and store them securely in a local ChromaDB collection for fast semantic search.
          </p>
          <button
            onClick={handleBuild}
            disabled={loading}
            className="px-8 py-4 bg-gradient-to-r from-fuchsia-600 to-rose-600 text-white rounded-xl font-bold shadow-lg shadow-fuchsia-200 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 text-lg"
          >
            Launch Vector Builder 🚀
          </button>
        </div>
      )}

      {loading && (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
          <div className="p-8 bg-gray-900 rounded-3xl shadow-2xl relative overflow-hidden ring-1 ring-white/10">
            {/* Animated Background Gradients */}
            <div className="absolute -top-24 -left-24 w-48 h-48 bg-fuchsia-500/20 rounded-full blur-3xl"></div>
            <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-rose-500/20 rounded-full blur-3xl"></div>

            <div className="absolute top-0 left-0 w-full h-1 bg-gray-800">
              <div 
                className="h-full bg-gradient-to-r from-fuchsia-500 via-rose-500 to-orange-500 transition-all duration-500 ease-out" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <div className="flex flex-col gap-6 relative z-10">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <div className="relative flex h-4 w-4">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fuchsia-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-fuchsia-500"></span>
                  </div>
                  Building Vector Embeddings
                </h3>
                <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 to-rose-400">
                  {progress}%
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-black/40 rounded-xl border border-white/5 backdrop-blur-sm">
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">System Status</p>
                  <p className="text-fuchsia-300 font-mono text-sm tracking-tight flex items-center gap-2">
                    <svg className="w-4 h-4 animate-spin text-fuchsia-500" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {currentStage}
                  </p>
                </div>

                <div className="p-4 bg-black/40 rounded-xl border border-white/5 backdrop-blur-sm min-h-[100px] flex flex-col justify-center">
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">Live Encoding Stream</p>
                  {currentDoc ? (
                    <div className="text-gray-200 text-sm font-mono leading-relaxed line-clamp-2 animate-in fade-in">
                      <span className="text-rose-400 mr-2 font-bold">~</span>
                      {currentDoc}
                    </div>
                  ) : (
                    <div className="flex gap-1.5 items-center mt-1">
                       <span className="w-1.5 h-1.5 rounded-full bg-gray-600 animate-bounce"></span>
                       <span className="w-1.5 h-1.5 rounded-full bg-gray-600 animate-bounce" style={{animationDelay: '0.2s'}}></span>
                       <span className="w-1.5 h-1.5 rounded-full bg-gray-600 animate-bounce" style={{animationDelay: '0.4s'}}></span>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress Steps Indicator */}
              <div className="flex items-center gap-2 pt-2">
                {['Load Model', 'Read Data', 'Encode Vectors', 'Save to DB'].map((stepName, i) => {
                  const stepProgress = (i + 1) * 25;
                  const isActive = progress >= stepProgress - 15;
                  return (
                    <div key={stepName} className="flex-1">
                      <div className={`h-1.5 rounded-full mb-2 transition-colors duration-500 ${isActive ? 'bg-fuchsia-500' : 'bg-gray-700'}`}></div>
                      <p className={`text-[10px] uppercase font-bold tracking-wider text-center transition-colors duration-500 ${isActive ? 'text-fuchsia-300' : 'text-gray-600'}`}>{stepName}</p>
                    </div>
                  );
                })}
              </div>

            </div>
          </div>
        </div>
      )}

      {result && !loading && (
        <div className={`p-6 rounded-2xl animate-in fade-in slide-in-from-bottom-4 ${result.error ? 'bg-red-50 border border-red-100' : 'bg-emerald-50 border border-emerald-100'}`}>
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-full ${result.error ? 'bg-red-100 text-red-600' : 'bg-emerald-100 text-emerald-600'}`}>
              {result.error ? (
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
              ) : (
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
              )}
            </div>
            <div className="flex-1">
              <h4 className={`text-lg font-bold ${result.error ? 'text-red-900' : 'text-emerald-900'}`}>
                {result.error ? 'Vector DB Generation Failed' : 'Knowledge Base Ready'}
              </h4>
              <p className={`mt-1 ${result.error ? 'text-red-700' : 'text-emerald-700'}`}>
                {result.error || 'Successfully processed all anonymized records into high-dimensional semantic space.'}
              </p>
              
              {!result.error && (
                <div className="mt-6 grid grid-cols-2 gap-4">
                  <div className="bg-white/60 p-4 rounded-xl">
                    <p className="text-emerald-600/70 text-xs font-bold uppercase tracking-wider">Documents Indexed</p>
                    <p className="text-3xl font-black text-emerald-700 mt-1">{result.document_count}</p>
                  </div>
                  <div className="bg-white/60 p-4 rounded-xl">
                    <p className="text-emerald-600/70 text-xs font-bold uppercase tracking-wider">Vectors Created</p>
                    <p className="text-3xl font-black text-emerald-700 mt-1">{result.vectors_created}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}