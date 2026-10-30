import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import { apiV2, type DatasetSummaryResponse } from '../lib/api-client-v2';
import { Database, Layers, ShieldCheck, Target } from 'lucide-react';

const BAND_COLORS: Record<string, string> = {
  Low: '#0072B2',
  Medium: '#E69F00',
  High: '#009E73',
};

const PANEL: CSSProperties = {
  background: 'var(--bg-secondary)',
  border: '1px solid var(--border-color)',
  borderRadius: 'var(--radius)',
  padding: '1.5rem',
  boxShadow: 'var(--shadow-sm)',
};

const CELL: CSSProperties = {
  padding: '0.55rem 0.65rem',
  borderBottom: '1px solid var(--border-color)',
};

const HEADER_CELL: CSSProperties = {
  padding: '0.65rem',
  textAlign: 'left',
  borderBottom: '2px solid var(--border-color)',
  fontWeight: 700,
};

function KpiCard({ label, value, hint, icon }: { label: string; value: string; hint: string; icon: ReactNode }) {
  return (
    <div style={{ ...PANEL, padding: '1.25rem' }} className="glass-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
        {icon}
      </div>
      <div style={{ fontSize: '1.85rem', fontWeight: 800, fontFamily: 'Outfit, sans-serif' }}>{value}</div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>{hint}</div>
    </div>
  );
}

function numeric(value: number | undefined, digits = 2): string {
  return typeof value === 'number' ? value.toFixed(digits) : '—';
}

export default function DataExplorerPage() {
  const [summary, setSummary] = useState<DatasetSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiV2
      .getDatasetSummary()
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          console.error('Failed to load dataset summary', e);
          setError(e instanceof Error ? e.message : 'Unknown error');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p role="status" style={{ padding: '2rem 0' }}>Loading dataset statistics…</p>;
  }

  if (error || !summary) {
    return (
      <p role="alert" style={{ padding: '2rem 0', color: 'var(--danger-color)' }}>
        Dataset statistics unavailable{error ? ` (${error})` : ''}. Sign in and retry.
      </p>
    );
  }

  const { dataset, split, class_balance, features, protected_attributes } = summary;
  const segments = split
    ? [
        { label: 'Train', count: split.train, color: '#0072B2' },
        { label: 'Cal-A', count: split.calibration.cal_a, color: '#56B4E9' },
        { label: 'Cal-B', count: split.calibration.cal_b, color: '#CC79A7' },
        { label: 'Test (locked)', count: split.test, color: '#D55E00' },
      ]
    : [];
  const splitTotal = segments.reduce((total, segment) => total + segment.count, 0);
  const maxBand = Math.max(...class_balance.map((band) => band.count), 1);
  const rows = summary.rows_loaded ?? dataset.total_rows;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', padding: '1.5rem 0' }}>
      <div style={PANEL}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Data Explorer</h1>
        <p style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {dataset.name} <code>v{dataset.semver}</code> — {dataset.description}
        </p>
        <p style={{ margin: '0.35rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
          Active variant <strong>{summary.variant}</strong> · License: {dataset.license} · {summary.notes}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <KpiCard
          label="Clean rows"
          value={rows.toLocaleString()}
          hint={`${dataset.variants?.length ?? 0} generator variants (${(dataset.variants ?? []).join(', ')})`}
          icon={<Database size={18} color="var(--primary-text)" />}
        />
        <KpiCard
          label="Model features"
          value={String(dataset.features.length)}
          hint="Identifiers and targets excluded"
          icon={<Layers size={18} color="var(--primary-text)" />}
        />
        <KpiCard
          label="Target columns"
          value={String(dataset.targets.length)}
          hint={dataset.targets.join(', ')}
          icon={<Target size={18} color="var(--primary-text)" />}
        />
        <KpiCard
          label="Protected attributes"
          value={String(protected_attributes.length)}
          hint={`${protected_attributes.join(', ')} — stored separately, never features`}
          icon={<ShieldCheck size={18} color="var(--primary-text)" />}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        <div style={PANEL}>
          <h2 style={{ margin: 0, fontSize: '1.05rem' }}>Frozen split composition</h2>
          {split ? (
            <>
              <div
                role="img"
                aria-label={`Split composition: ${segments
                  .map((segment) => `${segment.label} ${segment.count} rows`)
                  .join(', ')}`}
                style={{ display: 'flex', height: '1.5rem', borderRadius: '6px', overflow: 'hidden', margin: '0.9rem 0' }}
              >
                {segments.map((segment) => (
                  <div
                    key={segment.label}
                    title={`${segment.label}: ${segment.count.toLocaleString()} rows`}
                    style={{ width: `${(segment.count / (splitTotal || 1)) * 100}%`, background: segment.color }}
                  />
                ))}
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <caption style={{ textAlign: 'left', paddingBottom: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                  Seed {split.seed} · split hash <code>{split.split_hash?.slice(0, 12)}…</code>
                </caption>
                <tbody>
                  {segments.map((segment) => (
                    <tr key={segment.label}>
                      <td style={{ padding: '0.35rem 0' }}>
                        <span
                          aria-hidden="true"
                          style={{
                            display: 'inline-block',
                            width: '0.7rem',
                            height: '0.7rem',
                            background: segment.color,
                            borderRadius: '2px',
                            marginRight: '0.5rem',
                          }}
                        />
                        {segment.label}
                      </td>
                      <td style={{ padding: '0.35rem 0', textAlign: 'right', fontFamily: 'monospace' }}>
                        {segment.count.toLocaleString()}
                      </td>
                      <td style={{ padding: '0.35rem 0', textAlign: 'right', color: 'var(--text-secondary)' }}>
                        {((segment.count / (splitTotal || 1)) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : (
            <p style={{ color: 'var(--text-secondary)' }}>Split metadata unavailable.</p>
          )}
        </div>

        <div style={PANEL}>
          <h2 style={{ margin: 0, fontSize: '1.05rem' }}>Performance band balance</h2>
          <ul style={{ listStyle: 'none', padding: 0, margin: '0.9rem 0 0 0', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {class_balance.map((band) => (
              <li key={band.band}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>{band.band}</span>
                  <span style={{ fontFamily: 'monospace' }}>
                    {band.count.toLocaleString()} ({(band.share * 100).toFixed(1)}%)
                  </span>
                </div>
                <div style={{ background: 'rgba(127, 127, 127, 0.18)', borderRadius: '6px', height: '0.75rem', marginTop: '0.3rem' }}>
                  <div
                    style={{
                      width: `${(band.count / maxBand) * 100}%`,
                      background: BAND_COLORS[band.band] ?? 'var(--primary-color)',
                      height: '100%',
                      borderRadius: '6px',
                    }}
                  />
                </div>
              </li>
            ))}
          </ul>
          <p style={{ margin: '0.9rem 0 0 0', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Protected attributes are excluded from every model feature set and are never written to evidence artifacts.
          </p>
        </div>
      </div>

      <div style={PANEL}>
        <h2 style={{ margin: 0, fontSize: '1.05rem' }}>Feature statistics ({features.length})</h2>
        <div style={{ overflowX: 'auto', marginTop: '0.75rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                <th style={HEADER_CELL}>Feature</th>
                <th style={HEADER_CELL}>Type</th>
                <th style={{ ...HEADER_CELL, textAlign: 'right' }}>Missing</th>
                <th style={HEADER_CELL}>Distribution</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature) => (
                <tr key={feature.name}>
                  <td style={{ ...CELL, fontWeight: 600 }}>{feature.name}</td>
                  <td style={{ ...CELL, color: 'var(--text-secondary)' }}>{feature.kind}</td>
                  <td style={{ ...CELL, textAlign: 'right', fontFamily: 'monospace' }}>{feature.missing_pct}%</td>
                  <td style={{ ...CELL, fontFamily: 'monospace' }}>
                    {feature.kind === 'numeric'
                      ? `min ${numeric(feature.min)} · median ${numeric(feature.median)} · mean ${numeric(feature.mean)} · max ${numeric(feature.max)}`
                      : `${feature.categories} levels — ${(feature.top_values ?? [])
                          .map((entry) => `${entry.value} ${(entry.share * 100).toFixed(1)}%`)
                          .join(', ')}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
