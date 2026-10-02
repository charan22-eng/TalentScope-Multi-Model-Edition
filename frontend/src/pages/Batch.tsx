import { useState } from 'react';
import { batchPredict, type BatchPredictResponse } from '../lib/api-client';
import { ClassChip } from '../components/ui/ClassChip';

export default function BatchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<BatchPredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [filter, setFilter] = useState('');

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await batchPredict(file);
      setResults(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResults(null);
    setError(null);
  };

  const successCount = results?.results.filter((r: any) => r !== null).length || 0;
  const errorCount = results?.errors.filter((e: any) => e !== null).length || 0;
  const total = successCount + errorCount;
  
  // Naive column mapping UI (skipped full implementation for stub, we just pass the file)
  // Real implementation would parse CSV locally, allow mapping, then send mapped CSV.

  return (
    <div style={{ padding: '2rem 0' }}>
      <h2>Batch Predictions</h2>
      
      {!results && (
        <div style={{ marginBottom: '2rem', padding: '2rem', border: '2px dashed var(--border-color)', borderRadius: 'var(--radius)' }}>
          <h3>Import Wizard</h3>
          <p>Upload a CSV file with employee data to get batch predictions.</p>
          <input 
            type="file" 
            accept=".csv" 
            onChange={e => setFile(e.target.files?.[0] || null)} 
            style={{ marginBottom: '1rem', display: 'block' }}
          />
          <button 
            onClick={handleUpload} 
            disabled={!file || uploading}
            style={{ background: 'var(--primary-color)', color: 'white', padding: '0.75rem 1.5rem', borderRadius: 'var(--radius)', border: 'none', cursor: 'pointer' }}
          >
            {uploading ? 'Processing...' : 'Upload and Predict'}
          </button>
          
          {error && <p style={{ color: 'var(--danger-color)', marginTop: '1rem' }}>Upload Failed: {error}</p>}
        </div>
      )}

      {results && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>Validation Report</h3>
            <button onClick={handleReset} style={{ padding: '0.5rem 1rem', cursor: 'pointer' }}>New Upload</button>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
            <div style={{ flex: 1, padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
              <h4>Data Quality Score</h4>
              <p style={{ fontSize: '2rem', fontWeight: 'bold' }}>{Math.round((successCount / total) * 100)}%</p>
            </div>
            <div style={{ flex: 1, padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
              <h4>Success</h4>
              <p style={{ fontSize: '2rem', color: 'var(--success-color)', fontWeight: 'bold' }}>{successCount}</p>
            </div>
            <div style={{ flex: 1, padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
              <h4>Errors</h4>
              <p style={{ fontSize: '2rem', color: 'var(--danger-color)', fontWeight: 'bold' }}>{errorCount}</p>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <input 
              type="text" 
              placeholder="Filter by label or error..." 
              value={filter}
              onChange={e => setFilter(e.target.value)}
              style={{ padding: '0.5rem', width: '100%', maxWidth: '300px' }}
            />
          </div>

          <div style={{ height: '400px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: 'var(--radius)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-primary)' }}>
                <tr>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Row</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Status</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Result / Error Detail</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: total }).map((_, i) => {
                  const success = results.results[i];
                  const error = results.errors[i];
                  
                  if (filter) {
                    const str = success ? success.prediction.join(', ') : error?.error;
                    if (!str?.toLowerCase().includes(filter.toLowerCase())) return null;
                  }

                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.75rem' }}>{i + 1}</td>
                      <td style={{ padding: '0.75rem' }}>
                        {success ? <span style={{ color: 'var(--success-color)' }}>Success</span> : <span style={{ color: 'var(--danger-color)' }}>Failed</span>}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        {success && (
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            {success.prediction.map((p: string) => <ClassChip key={p} status={p as any} />)}
                            <span style={{ color: 'var(--text-secondary)' }}>({(success.confidence * 100).toFixed(1)}%)</span>
                          </div>
                        )}
                        {error && <span style={{ color: 'var(--danger-color)' }}>{error.error}</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
