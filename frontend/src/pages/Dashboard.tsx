import { useState, useEffect } from 'react';
import { ChartTableToggle } from '../components/ui/ChartTableToggle';
import axios from 'axios';

export default function DashboardPage() {
  const [sandbox, setSandbox] = useState(false);
  const [drift, setDrift] = useState<{ psi: number, status: string } | null>(null);

  useEffect(() => {
    const fetchDrift = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get('http://localhost:8000/analytics/drift', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setDrift(res.data);
      } catch (e) {
        console.error("Drift fetch error", e);
      }
    };
    fetchDrift();
  }, []);

  const data = sandbox 
    ? [ { name: 'Q1 (Synthetic)', value: 400 }, { name: 'Q2 (Synthetic)', value: 300 } ]
    : [ { name: 'Q1', value: 800 }, { name: 'Q2', value: 900 } ];

  return (
    <div style={{ padding: '2rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2>Analytics Dashboard</h2>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: sandbox ? 'var(--danger-color)' : 'var(--bg-secondary)', color: sandbox ? 'white' : 'inherit', padding: '0.5rem 1rem', borderRadius: 'var(--radius)' }}>
          <input type="checkbox" checked={sandbox} onChange={e => setSandbox(e.target.checked)} />
          {sandbox ? 'Synthetic Sandbox Mode Active' : 'Sandbox Mode'}
        </label>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
        <div style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h3 style={{ margin: '0 0 1rem 0' }}>Data Drift Monitoring (PSI)</h3>
          {drift ? (
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: drift.psi > 0.1 ? 'var(--danger-color)' : 'var(--success-color)' }}>
                {drift.psi.toFixed(4)}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>Status: {drift.status}</div>
            </div>
          ) : (
            <div>Loading drift data...</div>
          )}
        </div>
      </div>
      
      <ChartTableToggle title="Performance by Quarter" data={data} />
    </div>
  );
}
