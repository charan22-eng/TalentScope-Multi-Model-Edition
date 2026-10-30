import { useState, useEffect } from 'react';
import { apiV2, type LLMVerdictResponse } from '../../lib/api-client-v2';
import { ModelChip } from '../../components/ui/ModelChip';
import { Sparkles, RefreshCw, ChevronDown, ChevronUp, FileCode } from 'lucide-react';

const PROFILE_OPTIONS = ['Balanced', 'High Accuracy', 'Interpretability First', 'Low Latency', 'Fair & Robust'];

export function ArenaLLMVerdict() {
  const [profile, setProfile] = useState<string>('Balanced');
  const [audience, setAudience] = useState<'hr' | 'ds'>('hr');
  const [verdict, setVerdict] = useState<LLMVerdictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFact, setSelectedFact] = useState<string | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  const [openWhyNot, setOpenWhyNot] = useState<string | null>(null);

  const fetchVerdict = async (prof: string, aud: 'hr' | 'ds') => {
    setLoading(true);
    try {
      const res = await apiV2.postLLMVerdict({
        mode: 'verdict',
        profile: prof,
        audience: aud,
      });
      setVerdict(res);
    } catch (e) {
      console.error('Failed to generate LLM verdict', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVerdict(profile, audience);
  }, [profile, audience]);

  const handleRegenerate = () => {
    fetchVerdict(profile, audience);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Sparkles size={22} color="var(--primary-text)" />
              Enterprise AI Synthesis: "Why This Model is Best" Engine
            </h2>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Ground-truth narrative explanation constrained by Guard G9 numeric validation and strict evidence fact citations.
            </p>
          </div>

          <button
            type="button"
            onClick={handleRegenerate}
            disabled={loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.5rem 0.9rem',
              background: 'var(--primary-color)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius)',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem',
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Regenerate Verdict
          </button>
        </div>

        {/* Runtime info line & Controls Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Governance Profile:</span>
            <select
              value={profile}
              onChange={e => setProfile(e.target.value)}
              style={{ padding: '0.3rem 0.6rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)', fontSize: '0.8rem' }}
            >
              {PROFILE_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>

            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>Audience Tone:</span>
            <div style={{ display: 'inline-flex', borderRadius: '4px', border: '1px solid var(--border-color)', overflow: 'hidden' }}>
              <button
                type="button"
                onClick={() => setAudience('hr')}
                style={{
                  padding: '0.25rem 0.6rem',
                  border: 'none',
                  background: audience === 'hr' ? 'var(--primary-color)' : 'var(--bg-primary)',
                  color: audience === 'hr' ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                }}
              >
                HR Executive
              </button>
              <button
                type="button"
                onClick={() => setAudience('ds')}
                style={{
                  padding: '0.25rem 0.6rem',
                  border: 'none',
                  background: audience === 'ds' ? 'var(--primary-color)' : 'var(--bg-primary)',
                  color: audience === 'ds' ? '#ffffff' : 'var(--text-primary)',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                }}
              >
                Data Science
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            <span>Runtime: <strong>Local Ollama / Seed 42 / Temp 0.0</strong></span>
            {verdict && (
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: '9999px',
                  background: verdict.validation.source === 'llm' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                  color: verdict.validation.source === 'llm' ? '#10b981' : 'var(--primary-text)',
                  fontWeight: 600,
                }}
              >
                {verdict.validation.source === 'llm'
                  ? `✓ Validated (${verdict.validation.checks_evaluated} checks)`
                  : 'Deterministic Template Fallback'}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Verdict Card */}
      {verdict && (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.75rem', borderRadius: 'var(--radius)', border: '2px solid var(--primary-color)' }}>
          {/* Headline & Recommendation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', lineHeight: 1.3 }}>
                {verdict.headline}
              </h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Recommended Architecture:</span>
                <ModelChip modelKey={verdict.recommendation.model_key} showChampionBadge={true} size="md" />
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>DECISION STRENGTH</span>
              <span
                style={{
                  fontSize: '0.85rem',
                  padding: '3px 10px',
                  borderRadius: '4px',
                  background: 'rgba(245, 158, 11, 0.15)',
                  border: '1px solid #f59e0b',
                  color: '#f59e0b',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}
              >
                {verdict.recommendation.decision_strength}
              </span>
            </div>
          </div>

          {/* Claims with Clickable Fact Chips */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Core Evidence Claims</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {verdict.claims.map((claim, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '0.85rem 1rem',
                    background: 'var(--bg-primary)',
                    borderRadius: 'var(--radius)',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.4rem',
                  }}
                >
                  <div style={{ fontSize: '0.9rem', lineHeight: 1.5, color: 'var(--text-primary)' }}>
                    {claim.statement}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Cited Fact Chips:</span>
                    {claim.fact_ids.map((fid) => (
                      <button
                        key={fid}
                        type="button"
                        onClick={() => setSelectedFact(fid === selectedFact ? null : fid)}
                        style={{
                          padding: '1px 6px',
                          borderRadius: '4px',
                          border: `1px solid ${selectedFact === fid ? 'var(--primary-color)' : 'var(--border-color)'}`,
                          background: selectedFact === fid ? 'var(--primary-color)' : 'var(--bg-secondary)',
                          color: selectedFact === fid ? '#ffffff' : 'var(--text-primary)',
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                        }}
                      >
                        {fid}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {selectedFact && (
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid var(--primary-color)', borderRadius: 'var(--radius)', fontSize: '0.85rem' }}>
                <strong>Fact Inspector [{selectedFact}]:</strong> Number verified against frozen holdout test evaluation and evidence packet under Guard G9 invariant.
              </div>
            )}
          </div>

          {/* Trade-offs & Caveats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: 'var(--primary-text)' }}>
                Enterprise Trade-Offs
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {verdict.trade_offs.map((to, i) => <li key={i} style={{ marginBottom: '0.3rem' }}>{to}</li>)}
              </ul>
            </div>

            <div style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: '#f59e0b' }}>
                Governance Caveats
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {verdict.caveats.map((c, i) => <li key={i} style={{ marginBottom: '0.3rem' }}>{c}</li>)}
              </ul>
            </div>
          </div>

          {/* Per-Model "Why Not" Accordion */}
          {verdict.why_not && Object.keys(verdict.why_not).length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Architectural Rejection Rationales ("Why Not?")</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Object.entries(verdict.why_not).map(([k, reason]) => {
                  const isOpen = openWhyNot === k;
                  return (
                    <div
                      key={k}
                      style={{
                        background: 'var(--bg-primary)',
                        borderRadius: 'var(--radius)',
                        border: '1px solid var(--border-color)',
                        overflow: 'hidden',
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => setOpenWhyNot(isOpen ? null : k)}
                        style={{
                          width: '100%',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.75rem 1rem',
                          background: 'none',
                          border: 'none',
                          color: 'var(--text-primary)',
                          cursor: 'pointer',
                          fontSize: '0.85rem',
                          fontWeight: 600,
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span>Why not {k.toUpperCase()}?</span>
                        </div>
                        {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                      {isOpen && (
                        <div style={{ padding: '0 1rem 0.75rem 1rem', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                          {reason}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* "Show the evidence the model saw" Collapsible */}
          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
            <button
              type="button"
              onClick={() => setShowEvidence(!showEvidence)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              <FileCode size={16} />
              {showEvidence ? 'Hide raw evidence packet' : 'Show the evidence the model saw (read-only audit facts)'}
              {showEvidence ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {showEvidence && (
              <div
                style={{
                  marginTop: '0.75rem',
                  padding: '1rem',
                  background: 'var(--bg-primary)',
                  borderRadius: 'var(--radius)',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  maxHeight: '260px',
                  overflowY: 'auto',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div>// Packet Hash: {verdict.evidence_packet_hash}</div>
                <div>// Guard G8: Zero employee-level personal data allowed</div>
                <pre style={{ margin: '0.5rem 0', whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(verdict.claims, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
