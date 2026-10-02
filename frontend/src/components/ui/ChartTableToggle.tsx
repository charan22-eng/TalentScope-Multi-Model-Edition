import { useState } from 'react';

interface DataPoint {
  name: string;
  value: number;
}

interface ChartTableProps {
  title: string;
  data: DataPoint[];
}

export function ChartTableToggle({ title, data }: ChartTableProps) {
  const [view, setView] = useState<'chart' | 'table'>('chart');
  
  const maxValue = Math.max(...data.map(d => d.value), 1);

  return (
    <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>{title}</h3>
        <div>
          <button 
            onClick={() => setView('chart')} 
            style={{ fontWeight: view === 'chart' ? 'bold' : 'normal', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}
          >
            Chart
          </button>
          <span style={{ margin: '0 0.5rem' }}>|</span>
          <button 
            onClick={() => setView('table')} 
            style={{ fontWeight: view === 'table' ? 'bold' : 'normal', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}
          >
            Table
          </button>
        </div>
      </div>

      <div style={{ height: '300px' }}>
        {view === 'chart' ? (
          <div style={{ height: '100%', display: 'flex', alignItems: 'flex-end', gap: '1rem', padding: '1rem' }}>
            {data.map(d => (
              <div key={d.name} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{ height: '100%', display: 'flex', alignItems: 'flex-end', width: '100%', padding: '0 20%' }}>
                  <div style={{ width: '100%', background: 'var(--primary-color)', height: `${(d.value / maxValue) * 100}%`, borderRadius: '4px 4px 0 0' }}></div>
                </div>
                <div style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}>{d.name}</div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-primary)', padding: '1rem', borderRadius: 'var(--radius)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>Category</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {data.map(d => (
                  <tr key={d.name}>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>{d.name}</td>
                    <td style={{ padding: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>{d.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
