import { useState, useEffect, useRef } from 'react';

const DEFAULT_PROMPT = `You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Also extract 3 to 5 short sub-themes or topics mentioned.
Respond EXACTLY in this JSON format:
{
  "summary": "...",
  "sentiments": [
    {"sentiment": "Positive", "point": "..."}
  ],
  "subthemes": ["...", "..."]
}`;

const AVAILABLE_MODELS = [
  {
    id: 'gemma4:e4b',
    name: 'Gemma 4 E4B',
    provider: 'Google',
    description: 'Efficient 4-billion parameter model. Excellent at structured JSON output and analysis.',
    size: '~3 GB',
    speed: 'Fast',
    recommended: true
  },
  {
    id: 'gemma4:26b',
    name: 'Gemma 4 26B',
    provider: 'Google',
    description: 'Larger Gemma 4 option for higher-quality local analysis when your machine has enough memory.',
    size: 'Large',
    speed: 'Slow',
    recommended: false
  },
  {
    id: 'gemma3:4b',
    name: 'Gemma 3 4B',
    provider: 'Google',
    description: 'Previous generation Gemma. Reliable and well-tested for summary tasks.',
    size: '~3 GB',
    speed: 'Fast',
    recommended: false
  },
  {
    id: 'llama3.2:3b',
    name: 'Llama 3.2 3B',
    provider: 'Meta',
    description: 'Compact but capable model from Meta. Good general-purpose summarization.',
    size: '~2 GB',
    speed: 'Very Fast',
    recommended: false
  },
  {
    id: 'mistral:7b',
    name: 'Mistral 7B',
    provider: 'Mistral AI',
    description: 'Powerful 7B parameter model. Higher quality output but slower inference.',
    size: '~4.1 GB',
    speed: 'Moderate',
    recommended: false
  },
  {
    id: 'phi4-mini:latest',
    name: 'Phi-4 Mini',
    provider: 'Microsoft',
    description: 'Microsoft\'s efficient small model. Strong reasoning capabilities.',
    size: '~2.5 GB',
    speed: 'Fast',
    recommended: false
  }
];

export default function InsightGenerator({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [generating, setGenerating] = useState(false);

  // Configuration
  const [selectedModel, setSelectedModel] = useState('gemma4:e4b');
  const [customPrompt, setCustomPrompt] = useState(DEFAULT_PROMPT);
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [clearCache, setClearCache] = useState(false);
  const [allowModelDownload, setAllowModelDownload] = useState(false);

  const logRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const startGeneration = async () => {
    setGenerating(true);
    setLogs([]);
    setProgress(0);
    
    try {
      // If clearing cache, delete it first
      if (clearCache) {
        setLogs([`⚙️ Clearing cached insights...`]);
        try {
          await fetch('http://localhost:5001/api/clear-cache', { method: 'POST' });
          setLogs(prev => [...prev, `✅ Cache cleared. All insights will be regenerated.`]);
        } catch (e) {
          setLogs(prev => [...prev, `⚠️ Could not clear cache: ${e.message}`]);
        }
      }

      const { THEMES } = await import('../data/themes.js');
      const res = await fetch('http://localhost:5001/api/precompute-insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          themes: THEMES,
          ollama_model: selectedModel,
          custom_prompt: customPrompt !== DEFAULT_PROMPT ? customPrompt : '',
          allow_model_download: allowModelDownload
        })
      });
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(Boolean);
        
        for (let line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.status === 'progress') {
              setProgress(data.progress);
              setLogs(prev => [...prev, `[${data.theme}] ${data.message}`]);
            } else if (data.status === 'success') {
              setProgress(100);
              setLogs(prev => [...prev, "✅ " + data.message]);
              setTimeout(onComplete, 1500);
            } else if (data.status === 'error') {
              setLogs(prev => [...prev, "❌ Error: " + data.message]);
              setGenerating(false);
            }
          } catch (e) {}
        }
      }
    } catch (e) {
      setLogs(prev => [...prev, "❌ Connection Error: " + e.message]);
      setGenerating(false);
    }
  };

  const activeModel = AVAILABLE_MODELS.find(m => m.id === selectedModel);

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6 bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-gray-100 transition-all duration-500">
      
      {/* Header */}
      <div className="flex items-center space-x-4 pb-4 border-b border-gray-100">
        <div className="p-3 bg-gradient-to-tr from-violet-500 to-blue-500 text-white rounded-xl shadow-lg">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900">AI Insight Generation</h2>
          <p className="text-gray-500 text-sm mt-1">Run a local LLM to analyze themes and generate summaries from your vectorized data</p>
        </div>
      </div>

      {/* --- CONFIGURATION --- */}
      {!generating && progress === 0 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

          <div className="grid md:grid-cols-2 gap-6">

            {/* Model Selector */}
            <div className="space-y-4 p-6 bg-white border border-gray-100 shadow-sm rounded-2xl">
              <div className="flex items-center space-x-2 pb-2 border-b border-gray-50">
                <span className="text-xl">🤖</span>
                <h3 className="font-bold text-gray-800">Ollama Model</h3>
              </div>
              <div className="space-y-2 max-h-72 overflow-y-auto p-1">
                {AVAILABLE_MODELS.map(model => {
                  const isSelected = selectedModel === model.id;
                  return (
                    <label key={model.id} onClick={() => setSelectedModel(model.id)} className={`block p-3 rounded-xl border-2 cursor-pointer transition-all duration-200 ${isSelected ? 'border-violet-500 bg-violet-50/50 shadow-sm' : 'border-gray-100 hover:border-gray-200 bg-white'}`}>
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 flex items-center justify-center w-5 h-5 rounded-full flex-shrink-0 transition-colors ${isSelected ? 'bg-violet-500' : 'border-2 border-gray-300'}`}>
                          {isSelected && <div className="w-2 h-2 bg-white rounded-full"></div>}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className={`font-bold text-sm ${isSelected ? 'text-violet-900' : 'text-gray-700'}`}>{model.name}</p>
                            <span className="text-[10px] font-medium text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{model.provider}</span>
                            {model.recommended && <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">Default</span>}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">{model.description}</p>
                          <div className="flex gap-3 mt-1.5">
                            <span className="text-[10px] text-gray-400">📦 {model.size}</span>
                            <span className="text-[10px] text-gray-400">⚡ {model.speed}</span>
                          </div>
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                Model must be installed locally via <code className="bg-gray-100 px-1 py-0.5 rounded text-[10px]">ollama pull {selectedModel}</code>
              </p>
            </div>

            {/* Options Panel */}
            <div className="space-y-4">
              {/* Prompt Editor Toggle */}
              <div className="p-6 bg-white border border-gray-100 shadow-sm rounded-2xl space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-gray-50">
                  <div className="flex items-center space-x-2">
                    <span className="text-xl">📝</span>
                    <h3 className="font-bold text-gray-800">Analysis Prompt</h3>
                  </div>
                  <button
                    onClick={() => setShowPromptEditor(!showPromptEditor)}
                    className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${showPromptEditor ? 'bg-violet-100 text-violet-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                  >
                    {showPromptEditor ? 'Collapse' : 'Customize'}
                  </button>
                </div>

                {!showPromptEditor ? (
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <p className="text-xs text-gray-500 font-mono line-clamp-3">{customPrompt.substring(0, 180)}...</p>
                    <p className="text-[10px] text-gray-400 mt-2">Use <code className="bg-white px-1 py-0.5 rounded border text-violet-600">{'{theme_name}'}</code> as a placeholder for the current theme.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <textarea
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      rows={10}
                      className="w-full p-3 text-xs font-mono bg-gray-900 text-green-400 rounded-xl border border-gray-700 focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none"
                      placeholder="Enter your custom prompt..."
                    />
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] text-gray-400">Use <code className="bg-gray-100 px-1 py-0.5 rounded text-violet-600">{'{theme_name}'}</code> as a placeholder</p>
                      <button
                        onClick={() => setCustomPrompt(DEFAULT_PROMPT)}
                        className="text-[10px] font-semibold text-gray-500 hover:text-violet-600 transition-colors"
                      >
                        Reset to Default
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="p-6 bg-white border border-gray-100 shadow-sm rounded-2xl space-y-4">
                <div className="flex items-center space-x-2 pb-2 border-b border-gray-50">
                  <span className="text-xl">⚙️</span>
                  <h3 className="font-bold text-gray-800">Options</h3>
                </div>
                <label onClick={() => setClearCache(!clearCache)} className={`flex items-center p-3 rounded-xl border-2 cursor-pointer transition-all duration-200 ${clearCache ? 'border-amber-500 bg-amber-50/50' : 'border-gray-100 hover:border-gray-200 bg-white'}`}>
                  <div className={`flex items-center justify-center w-5 h-5 rounded flex-shrink-0 mr-3 transition-colors ${clearCache ? 'bg-amber-500' : 'border border-gray-300'}`}>
                    {clearCache && <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>}
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${clearCache ? 'text-amber-900' : 'text-gray-700'}`}>Clear Cached Insights</p>
                    <p className="text-xs text-gray-500">Force regeneration of all summaries, even if cached results exist.</p>
                  </div>
                </label>

                <label className={`flex items-center p-3 rounded-xl border-2 cursor-pointer transition-all duration-200 ${allowModelDownload ? 'border-violet-500 bg-violet-50/50' : 'border-gray-100 hover:border-gray-200 bg-white'}`}>
                  <input
                    type="checkbox"
                    checked={allowModelDownload}
                    onChange={(e) => setAllowModelDownload(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={`flex items-center justify-center w-5 h-5 rounded flex-shrink-0 mr-3 transition-colors ${allowModelDownload ? 'bg-violet-500' : 'border border-gray-300'}`}>
                    {allowModelDownload && <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>}
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${allowModelDownload ? 'text-violet-900' : 'text-gray-700'}`}>Pull Ollama model if missing</p>
                    <p className="text-xs text-gray-500">When disabled, generation fails before running if the selected Ollama model is not installed.</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Summary + Launch */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
            <div className="text-sm text-gray-600 flex items-center gap-2">
              <span className="font-semibold text-gray-800">{activeModel?.name}</span>
              <span className="text-gray-300">•</span>
              <span className="text-gray-500">7 themes</span>
              {clearCache && (
                <>
                  <span className="text-gray-300">•</span>
                  <span className="text-amber-600 font-medium text-xs">Cache will be cleared</span>
                </>
              )}
              {allowModelDownload && (
                <>
                  <span className="text-gray-300">•</span>
                  <span className="text-violet-600 font-medium text-xs">May pull model</span>
                </>
              )}
              {customPrompt !== DEFAULT_PROMPT && (
                <>
                  <span className="text-gray-300">•</span>
                  <span className="text-violet-600 font-medium text-xs">Custom prompt</span>
                </>
              )}
            </div>
            <button
              onClick={startGeneration}
              className="px-8 py-3 bg-gradient-to-r from-violet-600 to-blue-600 text-white rounded-xl font-bold shadow-lg shadow-violet-200 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300"
            >
              Generate Insights ✨
            </button>
          </div>
        </div>
      )}

      {/* --- GENERATING PROGRESS --- */}
      {generating && (
        <div className="space-y-6 animate-in fade-in zoom-in-95 duration-500">
          <div className="p-8 bg-gray-900 rounded-3xl shadow-2xl relative overflow-hidden ring-1 ring-white/10">
            {/* Animated Background */}
            <div className="absolute -top-24 -left-24 w-48 h-48 bg-violet-500/20 rounded-full blur-3xl"></div>
            <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl"></div>

            <div className="absolute top-0 left-0 w-full h-1 bg-gray-800">
              <div 
                className="h-full bg-gradient-to-r from-violet-500 via-blue-500 to-cyan-500 transition-all duration-500 ease-out" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            <div className="flex flex-col gap-5 relative z-10">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  {progress < 100 ? (
                    <div className="relative flex h-4 w-4">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-4 w-4 bg-violet-500"></span>
                    </div>
                  ) : (
                    <span className="text-emerald-400">✓</span>
                  )}
                  {progress < 100 ? 'Generating AI Insights' : 'Insights Complete!'}
                </h3>
                <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-blue-400">
                  {progress}%
                </span>
              </div>

              {/* Active model badge */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-violet-300 bg-violet-500/20 px-2 py-1 rounded-md">Model: {activeModel?.name}</span>
                <span className="text-xs font-medium text-blue-300 bg-blue-500/20 px-2 py-1 rounded-md">via Ollama</span>
              </div>

              {/* Logs */}
              <div ref={logRef} className="bg-black/50 rounded-xl p-4 h-56 overflow-y-auto font-mono text-xs border border-white/5 backdrop-blur-sm">
                {logs.map((log, i) => (
                  <div key={i} className={`py-0.5 ${log.startsWith('✅') ? 'text-emerald-400' : log.startsWith('❌') ? 'text-red-400' : log.startsWith('⚠️') ? 'text-amber-400' : log.startsWith('⚙️') ? 'text-blue-400' : 'text-green-400/80'}`}>
                    {log}
                  </div>
                ))}
                {generating && progress < 100 && (
                  <div className="text-gray-500 animate-pulse mt-1">▌</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* --- DONE STATE --- */}
      {!generating && progress === 100 && (
        <div className="p-6 bg-emerald-50 border border-emerald-100 rounded-2xl animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-emerald-100 text-emerald-600 rounded-full">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
            </div>
            <div>
              <h4 className="text-lg font-bold text-emerald-900">All Insights Generated Successfully</h4>
              <p className="text-emerald-700 mt-1">Theme summaries, sentiments, and sub-themes are cached and ready. The Overview dashboard will load instantly.</p>
              <p className="text-xs text-emerald-600 mt-2">Model used: <span className="font-semibold">{activeModel?.name}</span></p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
