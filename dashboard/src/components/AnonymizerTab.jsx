import { useState } from 'react';

export default function AnonymizerTab({ onComplete, existingAnonymized }) {
  const [file, setFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: upload, 2: select columns, 3: anonymizing
  const [result, setResult] = useState(null);
  const [preview, setPreview] = useState([]);

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files[0];
    if (!uploadedFile) return;

    setFile(uploadedFile);
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch('http://localhost:5000/api/inspect-file', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.status === 'success') {
        setColumns(data.columns);
        setPreview(data.preview);
        setStep(2);
        // Pre-select text columns (likely feedback columns)
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
    if (selectedColumns.includes(col)) {
      setSelectedColumns(selectedColumns.filter(c => c !== col));
    } else {
      setSelectedColumns([...selectedColumns, col]);
    }
  };

  const handleAnonymize = async () => {
    if (selectedColumns.length === 0) {
      setResult({ error: 'Select at least one column' });
      return;
    }

    setLoading(true);
    setStep(3);
    setResult(null);

    try {
      const response = await fetch('http://localhost:5000/api/anonymize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_columns: selectedColumns })
      });

      const data = await response.json();
      setResult(data);

      if (data.status === 'success') {
        // Notify parent that anonymization completed so next steps can be enabled
        if (typeof onComplete === 'function') {
          onComplete();
        }
        // keep showing the success result so user can see the message and optionally proceed
      }
    } catch (error) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">🔒 PII Anonymizer</h2>

      {/* Step 1: Upload */}
      {step === 1 && (
        <div className="space-y-4">
          <p className="text-gray-600">Upload a CSV file to anonymize</p>
          
          <div className="border-2 border-dashed border-blue-300 p-8 rounded-lg text-center hover:border-blue-500 cursor-pointer transition">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              disabled={loading}
              className="block w-full text-center cursor-pointer"
            />
            {file && <p className="mt-2 text-green-600">✓ {file.name}</p>}
          </div>

          {existingAnonymized && (
            <div className="mt-3">
              <p className="text-sm text-gray-600">An anonymized CSV was found on the server.</p>
              <button
                onClick={() => {
                  if (typeof onComplete === 'function') onComplete();
                }}
                className="mt-2 px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
              >
                Use existing anonymized CSV
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Select Columns */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded border border-blue-200">
            <p className="font-semibold mb-4">📋 Select columns to anonymize:</p>
            
            <div className="grid grid-cols-2 gap-3 mb-4">
              {columns.map(col => (
                <label key={col} className="flex items-center p-3 bg-white rounded border hover:bg-blue-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedColumns.includes(col)}
                    onChange={() => toggleColumn(col)}
                    className="w-4 h-4 mr-2"
                  />
                  <span className="text-sm">{col}</span>
                </label>
              ))}
            </div>

            {preview.length > 0 && (
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <p className="text-sm font-semibold mb-2">📌 Preview (first row):</p>
                <div className="space-y-2 text-xs">
                  {Object.entries(preview[0]).map(([key, value]) => (
                    <div key={key}>
                      <strong>{key}:</strong> {String(value).substring(0, 100)}...
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
            >
              ← Back
            </button>
            <button
              onClick={handleAnonymize}
              disabled={loading || selectedColumns.length === 0}
              className="flex-1 px-4 py-3 bg-blue-600 text-white rounded font-bold disabled:opacity-50 hover:bg-blue-700"
            >
              {loading ? '⏳ Processing...' : '🔒 Anonymize Selected'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Result */}
      {step === 3 && result && (
        <div className={`p-4 rounded ${result.error ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
          <strong>{result.error ? '❌ Error' : '✓ Success'}</strong>
          <p>{result.error || result.message}</p>
          {result.rows_processed && <p>Rows processed: {result.rows_processed}</p>}
          {result.columns_anonymized && <p>Columns: {result.columns_anonymized.join(', ')}</p>}
        </div>
      )}
    </div>
  );
}