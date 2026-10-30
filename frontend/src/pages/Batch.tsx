import { useState, useMemo } from 'react';
import { ModelChip } from '../components/ui/ModelChip';
import { ClassChip } from '../components/ui/ClassChip';
import { Download, Filter, Upload, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import { apiV2 } from '../lib/api-client-v2';

interface BatchRow {
  rowId: number;
  attendance: number;
  experience_years: number;
  training_hours: number;
  projects_completed: number;
  weekly_hours: number;
  prev_score: number;
  department: string;
  job_level: string;
  predictions: Record<string, 'Low' | 'Medium' | 'High'>;
  consensus: 'Low' | 'Medium' | 'High';
  hasDisagreement: boolean;
  isValid: boolean;
  validationError?: string;
}

const MODEL_KEYS = ['rf', 'boost', 'dt', 'knn', 'svm', 'logreg', 'linreg'];

export default function BatchPage() {
  const [selectedModel, setSelectedModel] = useState<string>('all');
  const [disagreementOnly, setDisagreementOnly] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 50;

  const [rows, setRows] = useState<BatchRow[]>([]);
  const [fileName, setFileName] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);

  const processFile = async (file: File) => {
    setProcessing(true);
    setFileName(file.name);
    try {
      const result = await apiV2.batchPredict(file, selectedModel === 'all' ? 'all' : selectedModel);
      const parsed = (result.results || []).map((item): BatchRow | null => {
        if (!item) return null;
        const predictions = item.predictions || { [result.model_key]: item.predicted_band || 'Unknown' };
        const values = Object.values(predictions);
        const counts = values.reduce<Record<string, number>>((acc, value) => {
          acc[value] = (acc[value] || 0) + 1;
          return acc;
        }, {});
        const consensus = (Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Medium') as BatchRow['consensus'];
        return {
          rowId: Number(item.row) + 1,
          attendance: 0,
          experience_years: 0,
          training_hours: 0,
          projects_completed: 0,
          weekly_hours: 0,
          prev_score: 0,
          department: '',
          job_level: '',
          predictions: predictions as BatchRow['predictions'],
          consensus,
          hasDisagreement: new Set(values).size > 1,
          isValid: true,
        };
      }).filter((row): row is BatchRow => row !== null);
      setRows(parsed);
      setPage(1);
    } finally {
      setProcessing(false);
    }
  };

  const handleGenerateSample = async () => {
    const headers = ['attendance', 'experience_years', 'training_hours', 'projects_completed', 'weekly_hours', 'prev_score', 'department', 'job_level'];
    const departments = ['Engineering', 'Sales', 'HR', 'Marketing', 'Finance'];
    const levels = ['Junior', 'Mid', 'Senior', 'Lead'];
    const lines = [headers.join(',')];
    for (let i = 0; i < 500; i += 1) {
      lines.push([85 + (i % 15), 1 + (i % 12), 10 + (i % 50), 1 + (i % 12), 35 + (i % 20), 1 + (i % 5), departments[i % departments.length], levels[i % levels.length]].join(','));
    }
    await processFile(new File([lines.join('\n')], 'sample_talent_batch_500.csv', { type: 'text/csv' }));
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    void processFile(file);
  };

  const filteredRows = useMemo(() => {
    return rows.filter(r => {
      if (disagreementOnly && !r.hasDisagreement) return false;
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          r.department.toLowerCase().includes(term) ||
          r.job_level.toLowerCase().includes(term) ||
          r.consensus.toLowerCase().includes(term)
        );
      }
      return true;
    });
  }, [rows, disagreementOnly, searchTerm]);

  const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;
  const paginatedRows = filteredRows.slice((page - 1) * pageSize, page * pageSize);

  const disagreementCount = useMemo(() => rows.filter(r => r.hasDisagreement).length, [rows]);

  const handleExportCSV = () => {
    if (rows.length === 0) return;
    const csvCell = (value: unknown) => {
      const text = String(value ?? '');
      const safe = /^[=+@]/.test(text) || (/^-/.test(text) && !/^-?(?:\d+(?:\.\d*)?|\.\d+)$/.test(text)) ? `'${text}` : text;
      return /[",\n]/.test(safe) ? `"${safe.replace(/"/g, '""')}"` : safe;
    };
    const headers = [
      'row_id', 'attendance', 'experience_years', 'training_hours', 'projects_completed',
      'weekly_hours', 'prev_score', 'department', 'job_level',
      ...MODEL_KEYS.map(k => `pred_${k}`),
      'consensus', 'has_disagreement'
    ];

    const csvLines = [headers.map(csvCell).join(',')];
    rows.forEach(r => {
      const line = [
        r.rowId, r.attendance, r.experience_years, r.training_hours, r.projects_completed,
        r.weekly_hours, r.prev_score, r.department, r.job_level,
        ...MODEL_KEYS.map(k => r.predictions[k]),
        r.consensus, r.hasDisagreement
      ];
      csvLines.push(line.map(csvCell).join(','));
    });

    const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `talentscope_batch_predictions_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1rem 0' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800 }}>Batch Inference & Consensus Auditing</h1>
        <p style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Evaluate up to 5,000 employee profiles simultaneously across all 7 machine learning models with automated disagreement detection.
        </p>
      </div>

      {/* Upload & Controls */}
      <div className="glass-panel" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <label
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              background: 'var(--primary-color)',
              color: '#ffffff',
              borderRadius: 'var(--radius)',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem',
            }}
          >
            <Upload size={16} />
            Upload CSV (Up to 5,000 rows)
            <input type="file" accept=".csv" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>

          <button
            type="button"
            onClick={handleGenerateSample}
            disabled={processing}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.5rem 0.85rem',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius)',
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            <RefreshCw size={14} className={processing ? 'animate-spin' : ''} />
            Generate 500-Row Sample
          </button>

          {fileName && (
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Loaded: <strong>{fileName}</strong> ({rows.length} rows)
            </span>
          )}
        </div>

        {rows.length > 0 && (
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <button
              type="button"
              onClick={handleExportCSV}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.85rem',
                background: '#10b981',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}
            >
              <Download size={14} />
              Export Predictions CSV
            </button>
          </div>
        )}
      </div>

      {/* Analytics Summary */}
      {rows.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Total Evaluated Rows</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>{rows.length}</div>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Unanimous Consensus</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 'bold', color: '#10b981' }}>
              {rows.length - disagreementCount} ({(((rows.length - disagreementCount) / rows.length) * 100).toFixed(1)}%)
            </div>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Split Decisions (Disagreements)</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 'bold', color: disagreementCount > 0 ? '#f59e0b' : 'var(--text-primary)' }}>
              {disagreementCount} ({((disagreementCount / rows.length) * 100).toFixed(1)}%)
            </div>
          </div>
        </div>
      )}

      {/* Filter and View Controls */}
      {rows.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', background: 'var(--bg-secondary)', padding: '0.75rem 1rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600 }}>
              <input
                type="checkbox"
                checked={disagreementOnly}
                onChange={e => { setDisagreementOnly(e.target.checked); setPage(1); }}
              />
              <Filter size={14} />
              Filter Disagreements Only ({disagreementCount})
            </label>

            <input
              type="text"
              placeholder="Search department, level, consensus..."
              value={searchTerm}
              onChange={e => { setSearchTerm(e.target.value); setPage(1); }}
              style={{ padding: '0.4rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
            />
          </div>

          {/* Model view column switcher */}
          <div style={{ display: 'flex', gap: '0.3rem', alignItems: 'center', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-secondary)', marginRight: '0.3rem' }}>Column View:</span>
            <button
              type="button"
              onClick={() => setSelectedModel('all')}
              style={{
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                border: '1px solid var(--border-color)',
                background: selectedModel === 'all' ? 'var(--primary-color)' : 'var(--bg-primary)',
                color: selectedModel === 'all' ? '#ffffff' : 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              All 7 Models
            </button>
            {MODEL_KEYS.map(k => (
              <button
                key={k}
                type="button"
                onClick={() => setSelectedModel(k)}
                style={{
                  padding: '0.2rem 0.5rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border-color)',
                  background: selectedModel === k ? 'var(--primary-color)' : 'var(--bg-primary)',
                  color: selectedModel === k ? '#ffffff' : 'var(--text-primary)',
                  cursor: 'pointer',
                }}
              >
                {k.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Batch Data Table */}
      {rows.length > 0 ? (
        <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto', maxHeight: '600px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-primary)', zIndex: 2 }}>
                <tr>
                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>#</th>
                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Dept</th>
                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Level</th>
                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Att%</th>
                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Proj</th>
                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Consensus</th>

                  {selectedModel === 'all' ? (
                    MODEL_KEYS.map(k => (
                      <th key={k} style={{ padding: '0.6rem 0.5rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>
                        <ModelChip modelKey={k} size="sm" showChampionBadge={false} />
                      </th>
                    ))
                  ) : (
                    <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>
                      <ModelChip modelKey={selectedModel} size="sm" />
                    </th>
                  )}

                  <th style={{ padding: '0.6rem 0.75rem', textAlign: 'center', borderBottom: '2px solid var(--border-color)' }}>Agreement</th>
                </tr>
              </thead>
              <tbody>
                {paginatedRows.map(r => (
                  <tr
                    key={r.rowId}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      background: r.hasDisagreement ? 'rgba(245, 158, 11, 0.04)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '0.6rem 0.75rem', fontFamily: 'monospace' }}>{r.rowId}</td>
                    <td style={{ padding: '0.6rem 0.75rem' }}>{r.department}</td>
                    <td style={{ padding: '0.6rem 0.75rem' }}>{r.job_level}</td>
                    <td style={{ padding: '0.6rem 0.75rem', textAlign: 'right' }}>{r.attendance}%</td>
                    <td style={{ padding: '0.6rem 0.75rem', textAlign: 'right' }}>{r.projects_completed}</td>
                    <td style={{ padding: '0.6rem 0.75rem', textAlign: 'center' }}>
                      <ClassChip status={r.consensus} />
                    </td>

                    {selectedModel === 'all' ? (
                      MODEL_KEYS.map(k => {
                        const pred = r.predictions[k];
                        const isOutlier = pred !== r.consensus;
                        return (
                          <td
                            key={k}
                            style={{
                              padding: '0.6rem 0.5rem',
                              textAlign: 'center',
                              background: isOutlier ? 'rgba(239, 68, 68, 0.1)' : undefined,
                            }}
                          >
                            <span style={{ fontWeight: isOutlier ? 700 : 400, color: isOutlier ? '#ef4444' : 'inherit' }}>
                              {pred}
                            </span>
                          </td>
                        );
                      })
                    ) : (
                      <td style={{ padding: '0.6rem 0.75rem', textAlign: 'center' }}>
                        <ClassChip status={r.predictions[selectedModel]} />
                      </td>
                    )}

                    <td style={{ padding: '0.6rem 0.75rem', textAlign: 'center' }}>
                      {r.hasDisagreement ? (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#f59e0b', fontSize: '0.75rem', fontWeight: 600 }}>
                          <AlertTriangle size={14} /> Split
                        </span>
                      ) : (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', color: '#10b981', fontSize: '0.75rem' }}>
                          <CheckCircle2 size={14} /> Unanimous
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1rem', borderTop: '1px solid var(--border-color)', background: 'var(--bg-primary)' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Showing {Math.min((page - 1) * pageSize + 1, filteredRows.length)} to {Math.min(page * pageSize, filteredRows.length)} of {filteredRows.length} rows
            </span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                style={{ padding: '0.3rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', cursor: page <= 1 ? 'not-allowed' : 'pointer', color: 'var(--text-primary)' }}
              >
                Previous
              </button>
              <span style={{ padding: '0.3rem 0.6rem', fontSize: '0.85rem' }}>
                Page {page} of {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                style={{ padding: '0.3rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', cursor: page >= totalPages ? 'not-allowed' : 'pointer', color: 'var(--text-primary)' }}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
          <Upload size={36} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }} />
          <p style={{ margin: 0 }}>Upload a CSV file or generate a 500-row sample to inspect batch multi-model predictions.</p>
        </div>
      )}
    </div>
  );
}
