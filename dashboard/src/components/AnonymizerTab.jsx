import { useState, useRef, useEffect } from 'react';

export default function AnonymizerTab({ onComplete, existingAnonymized }) {
  const [file, setFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [selectedLayers, setSelectedLayers] = useState(['presidio', 'eu-pii']);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [result, setResult] = useState(null);
  const [preview, setPreview] = useState([]);
  const [progress, setProgress] = useState(0);

  // Real-time stream states
  const [statusMessage, setStatusMessage] = useState('');
  const [currentPreview, setCurrentPreview] = useState('');

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch('http://localhost:5001/api/inspect-file', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.status === 'success') {
        setColumns(data.columns);
        setPreview(data.preview);
        setStep(2);
        const textCols = data.columns.filter(col => !['ID', 'Institution', 'academic_year', 'location', 'programme', 'study_mode', 'cohort'].includes(col));
        setSelectedColumns(textCols);
      } else {
        setResult({ error: data.error });
      }
    } catch (error) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const toggleColumn = (col) => {
    setSelectedColumns(prev =>
      prev.includes(col)
        ? prev.filter(c => c !== col)
        : [...prev, col]
    );
  };

  const toggleLayer = (layer) => {
    setSelectedLayers(prev =>
      prev.includes(layer)
        ? prev.filter(l => l !== layer)
        : [...prev, layer]
    );
  };

  const handleAnonymize = async () => {
    if (selectedColumns.length === 0) {
      setResult({ error: 'Select at least one column' });
      return;
    }

    if (selectedLayers.length === 0) {
      setResult({ error: 'Select at least one anonymization layer' });
      return;
    }

    setLoading(true);
    setStep(3);
    setResult(null);
    setProgress(0);
    setStatusMessage('Initializing stream...');
    setCurrentPreview('');

    try {
      const response = await fetch('http://localhost:5001/api/anonymize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selected_columns: selectedColumns,
          selected_layers: selectedLayers
        })
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
                  if (data.message) setStatusMessage(data.message);
                  if (data.preview) setCurrentPreview(data.preview);
                } else if (data.status === 'success') {
                  setResult(data);
                  setProgress(100);
                  setStatusMessage('Complete!');
                  setTimeout(() => {
                    if (typeof onComplete === 'function') onComplete();
                  }, 1500);
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
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6 bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-100 transition-all duration-500">
      <div className="flex items-center space-x-4 pb-4 border-b border-gray-100">
        <div className="p-3 bg-gradient-to-tr from-indigo-500 to-purple-500 text-white rounded-xl shadow-lg">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900">Data Anonymization Engine</h2>
          <p className="text-gray-500 text-sm mt-1">Transform sensitive survey data safely via layered masking</p>
        </div>
      </div>

      <div className="relative">
        {/* Step Indicator */}
        <div className="flex items-center justify-between mb-8 relative z-10">
          <div className="absolute top-1/2 -translate-y-1/2 left-0 w-full h-1 bg-gray-100 rounded-full -z-10"></div>
          <div className={`absolute top-1/2 -translate-y-1/2 left-0 h-1 bg-indigo-500 rounded-full -z-10 transition-all duration-700 ease-out`} style={{ width: step === 1 ? '0%' : step === 2 ? '50%' : '100%' }}></div>

          {[1, 2, 3].map(s => (
            <div key={s} className={`flex items-center justify-center w-10 h-10 rounded-full font-bold transition-all duration-500 shadow-md ${step >= s ? 'bg-indigo-600 text-white scale-110' : 'bg-white text-gray-400 border-2 border-gray-200'}`}>
              {step > s ? '✓' : s}
            </div>
          ))}
        </div>

        {/* --- STEP 1 --- */}
        {step === 1 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-500"></div>
              <div className="relative border-2 border-dashed border-indigo-200 bg-white/50 p-12 rounded-2xl text-center hover:border-indigo-500 cursor-pointer transition-all duration-300">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  disabled={loading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center justify-center space-y-4 pointer-events-none">
                  <div className="p-4 bg-indigo-50 text-indigo-500 rounded-full group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div className="space-y-1">
                    <p className="text-lg font-semibold text-gray-800">Drop your CSV file here or click to browse</p>
                    <p className="text-sm text-gray-500">Supports .csv files with standard delimiters</p>
                  </div>
                  {file && <p className="mt-4 inline-flex items-center text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full ring-1 ring-emerald-200">✓ {file.name}</p>}
                </div>
              </div>
            </div>

            {existingAnonymized && (
              <div className="flex items-center justify-between p-4 bg-indigo-50 border border-indigo-100 rounded-xl">
                <div className="flex items-center space-x-3 text-indigo-800">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  <span className="text-sm font-medium">An anonymized dataset is already available.</span>
                </div>
                <button
                  onClick={() => { if (typeof onComplete === 'function') onComplete(); }}
                  className="px-5 py-2 bg-white text-indigo-600 text-sm font-bold rounded-lg shadow-sm hover:shadow-md transition-all ring-1 ring-indigo-200 hover:bg-indigo-50"
                >
                  Skip & Use Existing
                </button>
              </div>
            )}
          </div>
        )}

        {/* --- STEP 2 --- */}
        {step === 2 && (
          <div className="space-y-8 animate-in fade-in slide-in-from-right-8 duration-500">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Columns Section */}
              <div className="space-y-4 p-6 bg-white border border-gray-100 shadow-sm rounded-2xl">
                <div className="flex items-center space-x-2 pb-2 border-b border-gray-50">
                  <span className="text-xl">📋</span>
                  <h3 className="font-bold text-gray-800">Select Columns</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-64 overflow-y-auto p-1">
                  {columns.map(col => {
                    const isSelected = selectedColumns.includes(col);
                    return (
                      <label
                        key={col}
                        className={`flex items-center p-3 rounded-xl border-2 cursor-pointer transition-all duration-200 ${isSelected ? 'border-indigo-500 bg-indigo-50/50' : 'border-gray-100 hover:border-gray-200 bg-white'}`}
                        role="checkbox"
                        aria-checked={isSelected}
                        tabIndex={0}
                        onClick={() => toggleColumn(col)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            toggleColumn(col);
                          }
                        }}
                      >
                        <div className={`flex items-center justify-center w-5 h-5 rounded flex-shrink-0 mr-3 transition-colors ${isSelected ? 'bg-indigo-500' : 'border border-gray-300'}`}>
                          {isSelected && <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>}
                        </div>
                        <span className={`text-sm truncate font-medium ${isSelected ? 'text-indigo-900' : 'text-gray-600'}`} title={col}>{col}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Layers Section */}
              <div className="space-y-4 p-6 bg-white border border-gray-100 shadow-sm rounded-2xl">
                <div className="flex items-center space-x-2 pb-2 border-b border-gray-50">
                  <span className="text-xl">🛡️</span>
                  <h3 className="font-bold text-gray-800">Security Layers</h3>
                </div>
                <div className="space-y-3">
                  <label
                    className={`flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${selectedLayers.includes('presidio') ? 'border-purple-500 bg-purple-50/50 shadow-sm' : 'border-gray-100 hover:border-gray-200 bg-white'}`}
                    role="checkbox"
                    aria-checked={selectedLayers.includes('presidio')}
                    tabIndex={0}
                    onClick={() => toggleLayer('presidio')}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggleLayer('presidio');
                      }
                    }}
                  >
                    <div className={`mt-0.5 flex items-center justify-center w-5 h-5 rounded flex-shrink-0 mr-4 transition-colors ${selectedLayers.includes('presidio') ? 'bg-purple-500' : 'border border-gray-300'}`}>
                      {selectedLayers.includes('presidio') && <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>}
                    </div>
                    <div>
                      <p className={`font-bold text-sm ${selectedLayers.includes('presidio') ? 'text-purple-900' : 'text-gray-700'}`}>Microsoft Presidio Engine</p>
                      <p className="text-xs text-gray-500 mt-1">Detects standard PII patterns (names, emails, phones, locations) globally.</p>
                    </div>
                  </label>

                  <label
                    className={`flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${selectedLayers.includes('eu-pii') ? 'border-purple-500 bg-purple-50/50 shadow-sm' : 'border-gray-100 hover:border-gray-200 bg-white'}`}
                    role="checkbox"
                    aria-checked={selectedLayers.includes('eu-pii')}
                    tabIndex={0}
                    onClick={() => toggleLayer('eu-pii')}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        toggleLayer('eu-pii');
                      }
                    }}
                  >
                    <div className={`mt-0.5 flex items-center justify-center w-5 h-5 rounded flex-shrink-0 mr-4 transition-colors ${selectedLayers.includes('eu-pii') ? 'bg-purple-500' : 'border border-gray-300'}`}>
                      {selectedLayers.includes('eu-pii') && <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>}
                    </div>
                    <div>
                      <p className={`font-bold text-sm ${selectedLayers.includes('eu-pii') ? 'text-purple-900' : 'text-gray-700'}`}>EU-PII-Safeguard AI</p>
                      <p className="text-xs text-gray-500 mt-1">Deep learning token-classification model fine-tuned for complex GDPR entities.</p>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            {preview.length > 0 && (
              <div className="p-5 bg-gray-50 border border-gray-200 rounded-xl">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Dataset Preview (Row 1)</p>
                <div className="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
                  {selectedColumns.slice(0, 4).map(col => (
                    <div key={col} className="min-w-[200px] max-w-[250px] p-3 bg-white rounded-lg shadow-sm border border-gray-100 flex-shrink-0">
                      <p className="text-xs font-bold text-indigo-600 mb-1 truncate">{col}</p>
                      <p className="text-sm text-gray-700 line-clamp-3">{String(preview[0][col] || '')}</p>
                    </div>
                  ))}
                  {selectedColumns.length > 4 && (
                    <div className="min-w-[100px] flex items-center justify-center text-sm font-medium text-gray-400">
                      +{selectedColumns.length - 4} more
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-4 pt-2">
              <button
                onClick={() => setStep(1)}
                className="px-6 py-3 bg-white text-gray-700 font-bold rounded-xl hover:bg-gray-50 border border-gray-200 transition-colors"
              >
                Go Back
              </button>
              <button
                onClick={handleAnonymize}
                disabled={loading || selectedColumns.length === 0 || selectedLayers.length === 0}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-bold shadow-lg shadow-indigo-200 disabled:opacity-50 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-center"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Initializing Models...
                  </span>
                ) : 'Launch Anonymization Engine 🚀'}
              </button>
            </div>
          </div>
        )}

        {/* --- STEP 3 --- */}
        {step === 3 && (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500">

            <div className="p-8 bg-gray-900 rounded-3xl shadow-2xl relative overflow-hidden ring-1 ring-white/10">
              <div className="absolute top-0 left-0 w-full h-1 bg-gray-800">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              <div className="flex flex-col md:flex-row gap-8 items-center md:items-start justify-between">

                <div className="flex-1 space-y-4 w-full">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3">
                      {progress < 100 ? (
                        <div className="relative flex h-4 w-4">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-4 w-4 bg-indigo-500"></span>
                        </div>
                      ) : (
                        <span className="text-emerald-400">✓</span>
                      )}
                      {progress < 100 ? 'Processing Stream' : 'Anonymization Complete'}
                    </h3>
                    <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
                      {progress}%
                    </span>
                  </div>

                  <div className="p-4 bg-white/5 rounded-xl border border-white/10 backdrop-blur-sm min-h-[120px] flex flex-col justify-center">
                    <p className="text-indigo-300 font-mono text-sm tracking-tight mb-2 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                      {statusMessage}
                    </p>
                    {currentPreview && (
                      <div className="mt-2 animate-in fade-in slide-in-from-bottom-2">
                        <p className="text-gray-400 text-xs mb-1 uppercase tracking-wider font-bold">Live Data Feed</p>
                        <p className="text-gray-200 text-sm font-mono leading-relaxed line-clamp-2">
                          <span className="text-emerald-400 mr-2">▶</span>
                          {currentPreview}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="w-full md:w-48 shrink-0 flex flex-col gap-3">
                  <div className={`p-3 rounded-lg border flex items-center gap-3 transition-colors ${progress > 10 ? 'bg-indigo-500/20 border-indigo-500/30' : 'bg-gray-800 border-gray-700'}`}>
                    <div className={`w-2 h-2 rounded-full ${progress > 10 ? 'bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)]' : 'bg-gray-600'}`}></div>
                    <span className={`text-sm font-medium ${progress > 10 ? 'text-indigo-200' : 'text-gray-500'}`}>Models Loaded</span>
                  </div>
                  <div className={`p-3 rounded-lg border flex items-center gap-3 transition-colors ${progress > 20 ? 'bg-purple-500/20 border-purple-500/30' : 'bg-gray-800 border-gray-700'}`}>
                    <div className={`w-2 h-2 rounded-full ${progress > 20 ? 'bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,0.8)]' : 'bg-gray-600'}`}></div>
                    <span className={`text-sm font-medium ${progress > 20 ? 'text-purple-200' : 'text-gray-500'}`}>Analyzing Text</span>
                  </div>
                  <div className={`p-3 rounded-lg border flex items-center gap-3 transition-colors ${progress === 100 ? 'bg-emerald-500/20 border-emerald-500/30' : 'bg-gray-800 border-gray-700'}`}>
                    <div className={`w-2 h-2 rounded-full ${progress === 100 ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' : 'bg-gray-600'}`}></div>
                    <span className={`text-sm font-medium ${progress === 100 ? 'text-emerald-200' : 'text-gray-500'}`}>Safeguard Applied</span>
                  </div>
                </div>

              </div>
            </div>

            {result?.error && (
              <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200 flex items-start gap-3">
                <svg className="w-5 h-5 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>
                <div>
                  <p className="font-bold">Anonymization Failed</p>
                  <p className="text-sm mt-1">{result.error}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}