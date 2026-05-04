import { useState, useEffect } from 'react';
import AnonymizerTab from '../components/AnonymizerTab';
import VectorDBBuilder from '../components/VectorDBBuilder'; 
import QueryTab from '../components/QueryTab';

export default function PipelineDemo() {
  const [activeTab, setActiveTab] = useState('anonymize');
  const [isAnonymized, setIsAnonymized] = useState(false);
  const [vectorDbReady, setVectorDbReady] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Check backend for existing anonymized CSV / vector DB and enable steps if present
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/status');
        const data = await res.json();
        if (data.status === 'success') {
          setIsAnonymized(Boolean(data.anonymized_exists));
          setVectorDbReady(Boolean(data.vector_db_exists));
        }
      } catch (e) {
        console.warn('Failed to fetch status:', e);
      }
    };
    checkStatus();
  }, []);

  const steps = [
    { id: 'anonymize', title: '1. Anonymize Data', icon: '🔒', enabled: true },
    { id: 'vectors', title: '2. Build Vector DB', icon: '🗄️', enabled: true },
    { id: 'insights', title: '3. Generate Insights', icon: '🧠', enabled: true },
    { id: 'query', title: '4. AI Query', icon: '✨', enabled: true },
  ];
  
  // Custom Insight Generator Component
  const InsightGenerator = ({ onComplete }) => {
    const [progress, setProgress] = useState(0);
    const [logs, setLogs] = useState([]);
    const [generating, setGenerating] = useState(false);
    
    const startGeneration = async () => {
      setGenerating(true);
      setLogs([]);
      setProgress(0);
      
      try {
        const { THEMES } = await import('../data/themes.js');
        const res = await fetch('http://localhost:5000/api/precompute-insights', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ themes: THEMES })
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
                setTimeout(onComplete, 1000);
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
    
    return (
      <div className="space-y-6">
        <h2 className="text-xl font-bold">Generate AI Insights</h2>
        <p className="text-sm text-gray-600">
          Precompute the theme frequencies and run the local Gemma model to generate all AI summaries at once. This ensures the Overview dashboard loads instantly!
        </p>
        
        {!generating && progress === 0 && (
          <button 
            onClick={startGeneration}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
          >
            Start Generation
          </button>
        )}
        
        {generating && (
          <div className="space-y-4">
             <div className="w-full bg-gray-200 rounded-full h-3">
               <div className="bg-blue-600 h-3 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
             </div>
             <p className="text-sm font-medium text-blue-700">{progress}% Complete</p>
             
             <div className="bg-gray-900 rounded-lg p-4 h-48 overflow-y-auto font-mono text-xs text-green-400">
               {logs.map((log, i) => (
                 <div key={i}>{log}</div>
               ))}
             </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Data Pipeline</h1>
          <p className="mt-2 text-sm text-gray-500">
            Securely anonymize feedback, vectorize the text, and query using AI.
          </p>
          {isProcessing && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-300 rounded-lg flex items-center">
              <div className="animate-spin mr-3 text-xl">⏳</div>
              <span className="text-blue-700 font-medium">Processing in backend...</span>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-4 border-b border-gray-200 pb-px" aria-label="Tabs">
          {steps.map((step) => (
            <button
              key={step.id}
              onClick={() => setActiveTab(step.id)}
              disabled={isProcessing}
              className={`
                flex items-center px-6 py-3 text-sm font-medium rounded-t-lg transition-colors
                ${activeTab === step.id 
                  ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}
                ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <span className="mr-2 text-lg">{step.icon}</span>
              {step.title}
            </button>
          ))}
        </nav>

        {/* Content Area */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 min-h-[500px]">
          {activeTab === 'anonymize' && (
            <AnonymizerTab existingAnonymized={isAnonymized} onComplete={() => {
              setIsAnonymized(true);
            }} />
          )}
          
          {activeTab === 'vectors' && (
            <VectorDBBuilder 
              onSuccess={() => {
                setVectorDbReady(true);
                setActiveTab('insights');
              }} 
            />
          )}
          
          {activeTab === 'insights' && (
             <InsightGenerator onComplete={() => setActiveTab('query')} />
          )}
          
          {activeTab === 'query' && (
            <QueryTab />
          )}
        </div>

      </div>
    </div>
  );
}