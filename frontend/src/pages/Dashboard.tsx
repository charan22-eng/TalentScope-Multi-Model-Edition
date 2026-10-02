import { useState } from 'react';
import { ChartTableToggle } from '../components/ui/ChartTableToggle';

export default function DashboardPage() {
  const [sandbox, setSandbox] = useState(false);

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

      <ChartTableToggle title="Performance by Quarter" data={data} />
    </div>
  );
}
