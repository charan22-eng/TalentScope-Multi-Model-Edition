

export default function ModelLabPage() {
  return (
    <div style={{ padding: '2rem 0' }}>
      <h2>Model Lab</h2>
      <p style={{ background: 'var(--bg-secondary)', padding: '1rem', borderLeft: '4px solid var(--primary-color)' }}>
        <strong>Benchmark Note:</strong> The numbers below match `comparison.json` strictly.
      </p>
      
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '2rem' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '0.75rem', borderBottom: '2px solid var(--border-color)' }}>Metric</th>
            <th style={{ textAlign: 'left', padding: '0.75rem', borderBottom: '2px solid var(--border-color)' }}>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>F1-Score (Macro)</td>
            <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>0.655</td>
          </tr>
          <tr>
            <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>Extreme Errors</td>
            <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>0.9%</td>
          </tr>
          <tr>
            <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>Coverage (Conformal)</td>
            <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>90.5%</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
