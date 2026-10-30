import axios from 'axios';
import { ensureAuthToken } from './auth-bootstrap';

export interface EmployeeFeatures {
  attendance: number;
  experience_years: number;
  training_hours: number;
  projects_completed: number;
  weekly_hours: number;
  prev_score: number | null;
  department: string;
  job_level: string;
  peer_feedback?: number;
  tasks_on_time_pct?: number;
  certifications?: number;
}

export interface ModelPrediction {
  model_key: string;
  model_name?: string;
  prediction_set: ('Low' | 'Medium' | 'High')[];
  top_class: 'Low' | 'Medium' | 'High';
  probabilities: { Low: number; Medium: number; High: number };
  stability_index: number;
  performance_index: number;
  review_flag: boolean;
  is_champion?: boolean;
}

export interface PredictAllResponse {
  predictions: Record<string, ModelPrediction>;
  consensus_class: 'Low' | 'Medium' | 'High';
  agreement_count: number;
  total_models: number;
  agreement_rate: number;
  split_decision: boolean;
  champion_prediction: ModelPrediction;
  models_evaluated: string[];
  latency_ms?: number;
}

export interface ExplainResponse {
  model_key: string;
  explanation_type: 'native' | 'partial' | 'model_agnostic' | 'similar_cases' | string;
  summary_hr: string;
  summary_ds: string;
  native_explanation?: Record<string, unknown>;
  local_attribution?: Record<string, number>;
  counterfactuals?: {
    feature: string;
    original_value: number | string;
    proposed_value: number | string;
    delta: number | string;
    target_class: string;
  }[];
  similar_cases?: {
    id: number | string;
    distance: number;
    true_band: string;
    predicted_band: string;
    note?: string;
    department?: string;
    job_level?: string;
  }[];
  key_drivers?: string[];
  actionable_guidance?: string;
  llm_metadata?: {
    source: string;
    model: string;
    latency_ms?: number;
  };
}

export interface LeaderboardModel {
  key: string;
  name: string;
  label?: string;
  family: string;
  macro_f1: number;
  macro_f1_ci_low: number;
  macro_f1_ci_high: number;
  accuracy: number;
  qwk: number;
  balanced_accuracy?: number;
  brier_score?: number;
  ece?: number;
  ovr_auc?: number;
  exact_rate?: number;
  adjacent_rate?: number;
  extreme_rate?: number;
  f1_low?: number;
  f1_medium?: number;
  f1_high?: number;
  per_class?: Record<string, { f1: number; precision: number; recall: number; support: number }>;
  inference_latency_p95_ms?: number;
  inference_latency_p50_ms?: number;
  batch_latency_ms?: number;
  training_time_sec?: number;
  model_size_kb?: number;
  rank?: number;
  is_champion?: boolean;
}

export interface LeaderboardResponse {
  variant: string;
  metrics: LeaderboardModel[];
  champion_key: string;
  champion_rule: string;
  confirmation?: Record<string, unknown>;
}

export interface MCDAResult {
  weights_used: Record<string, number>;
  profile_name: string;
  ranked_models: {
    key: string;
    composite_score: number;
    rank: number;
    rank1_probability: number;
    decision_strength: 'clear' | 'marginal' | 'none';
  }[];
  winner: string;
  decision_strength: 'clear' | 'marginal' | 'none';
  decision_rule: string;
}

export interface LLMVerdictResponse {
  headline: string;
  recommendation: {
    model_key: string;
    confidence: 'high' | 'medium' | 'low' | 'clear' | 'marginal' | 'none';
    decision_strength: 'clear' | 'marginal' | 'none';
  };
  claims: { statement: string; fact_ids: string[] }[];
  trade_offs: string[];
  caveats: string[];
  why_not: Record<string, string>;
  validation: {
    passed: boolean;
    errors: string[];
    source: 'llm' | 'template_fallback' | 'cache';
    checks_evaluated: number;
  };
  evidence_packet_hash: string;
}

export interface DatasetFeatureStat {
  name: string;
  kind: 'numeric' | 'categorical';
  missing_pct: number;
  min?: number;
  median?: number;
  mean?: number;
  max?: number;
  categories?: number;
  top_values?: { value: string; share: number }[];
}

export interface DatasetSummaryResponse {
  dataset: {
    name: string;
    semver: string;
    description?: string;
    variants?: string[];
    default_variant?: string;
    total_rows: number;
    features: string[];
    targets: string[];
    license?: string;
  };
  variant: string;
  split: {
    seed: number;
    n_rows: number;
    train: number;
    calibration: { cal_a: number; cal_b: number };
    test: number;
    dataset_sha256?: string;
    split_hash?: string;
  } | null;
  class_balance: { band: string; count: number; share: number }[];
  features: DatasetFeatureStat[];
  protected_attributes: string[];
  rows_loaded?: number;
  notes: string;
}

type RawPrediction = {
  model_key: string;
  predicted_band: 'Low' | 'Medium' | 'High';
  confidence: number;
  prediction_set: ('Low' | 'Medium' | 'High')[];
  probabilities: Record<string, number>;
  stability_score: number;
  performance_index: number;
};

const API_ORIGIN = import.meta.env.VITE_API_ORIGIN || 'http://localhost:8000';
const API_V2_BASE = `${API_ORIGIN.replace(/\/$/, '')}/api/v2`;

export const apiClientV2 = axios.create({
  baseURL: API_V2_BASE,
  headers: { 'Content-Type': 'application/json' },
});

apiClientV2.interceptors.request.use(async (config) => {
  let token = localStorage.getItem('token');
  if (!token) {
    token = await ensureAuthToken();
  }
  if (token && config.headers) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClientV2.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as { _retry?: boolean; headers: Record<string, string> } | undefined;
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      const newToken = await ensureAuthToken(true);
      if (newToken && originalRequest.headers) {
        if (typeof (originalRequest.headers as unknown as { set?: unknown }).set === 'function') {
          (originalRequest.headers as unknown as { set: (k: string, v: string) => void }).set(
            'Authorization',
            `Bearer ${newToken}`
          );
        } else {
          (originalRequest.headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
        }
        return apiClientV2(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);

function normalizePrediction(raw: RawPrediction, championKey?: string): ModelPrediction {
  const probabilities = {
    Low: Number(raw.probabilities.Low ?? 0),
    Medium: Number(raw.probabilities.Medium ?? 0),
    High: Number(raw.probabilities.High ?? 0),
  };
  const stability = Number(raw.stability_score ?? 0);
  return {
    model_key: raw.model_key,
    prediction_set: raw.prediction_set,
    top_class: raw.predicted_band,
    probabilities,
    stability_index: stability,
    performance_index: Number(raw.performance_index ?? 0),
    review_flag: stability < 70 || raw.prediction_set.length > 1,
    is_champion: raw.model_key === championKey,
  };
}

function normalizeLeaderboard(raw: Record<string, unknown>): LeaderboardResponse {
  const confidenceIntervals = (raw.confidence_intervals || {}) as Record<string, Record<string, number[]>>;
  const metrics = ((raw.metrics || []) as Record<string, unknown>[]).map((row, index) => {
    const key = String(row.key);
    const ci = confidenceIntervals[key] || {};
    const f1Ci = ci.macro_f1_ci || [Number(row.macro_f1 || 0), Number(row.macro_f1 || 0)];
    const perClass = (row.per_class || {}) as Record<string, Record<string, number>>;
    return {
      key,
      name: String(row.label || key),
      label: String(row.label || key),
      family: String(row.family || ''),
      macro_f1: Number(row.macro_f1 || 0),
      macro_f1_ci_low: Number(f1Ci[0] || 0),
      macro_f1_ci_high: Number(f1Ci[1] || 0),
      accuracy: Number(row.accuracy || 0),
      qwk: Number(row.qwk || 0),
      balanced_accuracy: Number(row.balanced_accuracy || 0),
      brier_score: Number(row.brier ?? row.brier_score ?? 0),
      ece: Number(row.ece ?? 0),
      ovr_auc: Number(row.roc_auc_ovr ?? row.ovr_auc ?? 0),
      exact_rate: Number(row.exact_share ?? row.exact_rate ?? 0),
      adjacent_rate: Number(row.adjacent_share ?? row.adjacent_rate ?? 0),
      extreme_rate: Number(row.extreme_share ?? row.extreme_rate ?? 0),
      f1_low: perClass.Low?.f1 !== undefined ? Number(perClass.Low.f1) : undefined,
      f1_medium: perClass.Medium?.f1 !== undefined ? Number(perClass.Medium.f1) : undefined,
      f1_high: perClass.High?.f1 !== undefined ? Number(perClass.High.f1) : undefined,
      per_class: row.per_class ? (row.per_class as Record<string, { f1: number; precision: number; recall: number; support: number }>) : undefined,
      inference_latency_p95_ms: Number(row.latency_single_p95_ms || 0),
      inference_latency_p50_ms: Number(row.latency_single_p50_ms || 0),
      batch_latency_ms: Number(row.latency_batch_5000_ms || 0),
      training_time_sec: Number(row.tuning_time_sec || 0),
      model_size_kb: Number(row.model_size_bytes || 0) / 1024,
      rank: index + 1,
    } satisfies LeaderboardModel;
  });
  const championKey = String(raw.champion_key || 'boost');
  return {
    variant: String(raw.metrics && (raw.metrics as Record<string, unknown>[])[0]?.variant || 'nonlinear'),
    metrics: metrics.map((metric) => ({ ...metric, is_champion: metric.key === championKey })),
    champion_key: championKey,
    champion_rule: String(raw.champion_rule || 'ADR-009 Multi-Criteria Decision Analysis'),
  };
}

function normalizeExplain(raw: Record<string, unknown>): ExplainResponse {
  const persona = (raw.persona_summaries || {}) as Record<string, string>;
  const similar = (raw.similar_cases || {}) as Record<string, unknown>;
  const neighbors = Array.isArray(similar.neighbors) ? similar.neighbors : [];
  const rawCfs = Array.isArray(raw.counterfactuals) ? raw.counterfactuals : [];

  const counterfactuals = rawCfs.map((item: Record<string, unknown>) => {
    let feature = String(item.feature || '');
    let originalValue: number | string = item.original_value !== undefined ? (item.original_value as number | string) : '';
    let proposedValue: number | string = item.proposed_value !== undefined ? (item.proposed_value as number | string) : '';
    let delta: number | string = item.delta !== undefined ? (item.delta as number | string) : '';
    const targetClass = String(item.target_class || 'High');

    if (!feature && item.changes && typeof item.changes === 'object') {
      const keys = Object.keys(item.changes);
      if (keys.length > 0) {
        feature = keys[0];
        proposedValue = Number((item.changes as Record<string, number>)[feature]);
      }
    }
    return {
      feature: feature || 'training_hours',
      original_value: originalValue,
      proposed_value: proposedValue,
      delta: delta,
      target_class: targetClass,
    };
  });

  return {
    model_key: String(raw.model_key || 'rf'),
    explanation_type: String(raw.explanation_type || 'model_agnostic'),
    summary_hr: persona.hr_summary || 'No HR summary available.',
    summary_ds: persona.datascience_summary || 'No data-science summary available.',
    native_explanation: (raw.native_explanation || {}) as Record<string, unknown>,
    local_attribution: (raw.local_attribution || {}) as Record<string, number>,
    counterfactuals,
    similar_cases: neighbors.map((item, index) => {
      const neighbor = item as Record<string, unknown>;
      const band = String(neighbor.performance || 'Unknown');
      return {
        id: String(neighbor.employee_id || index + 1),
        distance: Number(neighbor.distance || 0),
        true_band: band,
        predicted_band: band,
        department: typeof neighbor.department === 'string' ? neighbor.department : undefined,
        job_level: typeof neighbor.job_level === 'string' ? neighbor.job_level : undefined,
      };
    }),
    key_drivers: Array.isArray(raw.key_drivers) ? (raw.key_drivers as string[]) : undefined,
    actionable_guidance: typeof raw.actionable_guidance === 'string' ? raw.actionable_guidance : undefined,
    llm_metadata: (raw.llm_metadata || undefined) as ExplainResponse['llm_metadata'],
  };
}

function normalizeLLM(raw: Record<string, unknown>): LLMVerdictResponse {
  const verdict = (raw.verdict || {}) as Record<string, unknown>;
  const recommendation = (verdict.recommendation || {}) as Record<string, unknown>;
  const validation = (raw.validation || {}) as Record<string, unknown>;
  const confidence = String(recommendation.confidence || 'none') as LLMVerdictResponse['recommendation']['confidence'];
  return {
    headline: String(verdict.headline || 'No verdict available'),
    recommendation: {
      model_key: String(recommendation.model_key || 'boost'),
      confidence,
      decision_strength: (String(recommendation.decision_strength || confidence) as 'clear' | 'marginal' | 'none'),
    },
    claims: ((verdict.claims || []) as Record<string, unknown>[]).map((claim) => ({
      statement: String(claim.statement || claim.text || ''),
      fact_ids: (claim.fact_ids || []) as string[],
    })),
    trade_offs: ((verdict.trade_offs || verdict.tradeoffs || []) as (string | Record<string, unknown>)[]).map((item) =>
      typeof item === 'string' ? item : String(item.text || '')
    ),
    caveats: ((verdict.caveats || []) as (string | Record<string, unknown>)[]).map((item) =>
      typeof item === 'string' ? item : String(item.text || '')
    ),
    why_not: (verdict.why_not || {}) as Record<string, string>,
    validation: {
      passed: Boolean(validation.valid ?? validation.passed ?? true),
      errors: (validation.errors || []) as string[],
      source: raw.source === 'live_llm' ? 'llm' : raw.source === 'cache' ? 'cache' : 'template_fallback',
      checks_evaluated: Number(validation.checks_evaluated || 0),
    },
    evidence_packet_hash: String(raw.evidence_packet_hash || ''),
  };
}

export const apiV2 = {
  getModels: async () => (await apiClientV2.get('/models')).data,

  predictSingle: async (modelKey: string, features: EmployeeFeatures): Promise<ModelPrediction> => {
    const res = await apiClientV2.post<RawPrediction>('/predict', { model_key: modelKey, features });
    return normalizePrediction(res.data);
  },

  predictAll: async (features: EmployeeFeatures): Promise<PredictAllResponse> => {
    const res = await apiClientV2.post('/predict/all', features);
    const raw = res.data as {
      predictions: Record<string, RawPrediction>;
      consensus_band: 'Low' | 'Medium' | 'High';
      agreement_rate: number;
      split_decision: boolean;
      champion_key: string;
      champion_prediction: RawPrediction;
      latency_ms: number;
    };
    const modelsEvaluated = Object.keys(raw.predictions);
    const predictions = Object.fromEntries(
      modelsEvaluated.map((key) => [key, normalizePrediction(raw.predictions[key], raw.champion_key)])
    );
    return {
      predictions,
      consensus_class: raw.consensus_band,
      agreement_count: Math.round(raw.agreement_rate * modelsEvaluated.length),
      total_models: modelsEvaluated.length,
      agreement_rate: raw.agreement_rate,
      split_decision: raw.split_decision,
      champion_prediction: normalizePrediction(raw.champion_prediction, raw.champion_key),
      models_evaluated: modelsEvaluated,
      latency_ms: raw.latency_ms,
    };
  },

  explain: async (modelKey: string, features: EmployeeFeatures, k = 5): Promise<ExplainResponse> => {
    const res = await apiClientV2.post('/explain', { model_key: modelKey, features, k });
    return normalizeExplain(res.data);
  },

  getCompare: async (topic: string): Promise<Record<string, unknown>> => {
    const raw = (await apiClientV2.get(`/compare/${topic}`)).data as Record<string, unknown>;
    if (topic === 'leaderboard') return normalizeLeaderboard(raw) as unknown as Record<string, unknown>;
    if (topic === 'importance') return { ...raw, importance_matrix: raw.importances, spearman_matrix: raw.spearman_agreement_matrix };
    if (topic === 'head2head' || topic === 'pairwise') {
      const pairMap = (raw.pair_map || {}) as Record<string, Record<string, unknown>>;
      return {
        ...raw,
        pairs: Object.fromEntries(Object.entries(pairMap).map(([key, value]) => [key, {
          model_a: String(value.model_a ?? ''),
          model_b: String(value.model_b ?? ''),
          mcnemar_statistic: Number(value.stat ?? 0),
          p_value: Number(value.raw_p ?? 1),
          holm_p_value: Number(value.holm_p ?? 1),
          // In epk/stats.py:
          // b_discordant = model_a wrong, model_b correct
          // c_discordant = model_a correct, model_b wrong
          discordant_a_b: Number(value.c_discordant ?? 0),
          discordant_b_a: Number(value.b_discordant ?? 0),
          is_significant: Boolean(value.significant),
        }])),
      };
    }
    if (topic === 'confusion') {
      return {
        ...raw,
        matrices: Object.fromEntries(Object.entries(raw).map(([key, value]) => [key, (value as Record<string, unknown>).matrix])),
      };
    }
    if (topic === 'sensitivity') {
      const variants = (raw.variants || {}) as Record<string, Record<string, unknown>>;
      const linear = (variants.linear?.rankings || {}) as Record<string, number>;
      const nonlinear = (variants.nonlinear?.rankings || {}) as Record<string, number>;
      const noisy = (variants.noisy_overlap?.rankings || {}) as Record<string, number>;
      return {
        ...raw,
        rankings: Object.keys(linear).map((modelKey) => ({ modelKey, linearRank: linear[modelKey], nonlinearRank: nonlinear[modelKey], noisyRank: noisy[modelKey] })),
        kendall_tau: {
          linearVsNonlinear: Number((raw.kendall_tau as Record<string, Record<string, unknown>>)?.linear_vs_nonlinear?.tau || 0),
          nonlinearVsNoisy: Number((raw.kendall_tau as Record<string, Record<string, unknown>>)?.nonlinear_vs_noisy_overlap?.tau || 0),
        },
      };
    }
    if (topic === 'curves') {
      return {
        ...raw,
        metrics: Object.entries(raw).map(([key, value]) => {
          const item = value as Record<string, number>;
          return {
            key,
            name: key.toUpperCase(),
            brier_score: item.brier,
            ece: item.ece,
            ovr_auc: item.roc_auc_ovr,
          };
        }),
      };
    }
    return raw;
  },

  postMCDA: async (weights: Record<string, number>, profile = 'Custom'): Promise<MCDAResult> => {
    const res = await apiClientV2.post('/compare/mcda', { weights, profile });
    return res.data;
  },

  getDatasetSummary: async (): Promise<DatasetSummaryResponse> => (await apiClientV2.get('/dataset/summary')).data,

  getSurface: async (modelKey: string, resolution = 40) => (await apiClientV2.get('/viz/surface', { params: { model_key: modelKey, grid_size: resolution } })).data,
  getPCA: async () => (await apiClientV2.get('/viz/pca')).data,
  getLLMHealth: async () => (await apiClientV2.get('/llm/health')).data,
  getLLMModels: async () => (await apiClientV2.get('/llm/models')).data,

  postLLMVerdict: async (payload: { mode?: string; profile?: string; audience?: string; rejected_model?: string }): Promise<LLMVerdictResponse> => {
    const res = await apiClientV2.post('/llm/verdict', payload);
    return normalizeLLM(res.data);
  },

  triggerRetrain: async (profile: 'fast' | 'standard') => (await apiClientV2.post('/retrain', { profile })).data,

  batchPredict: async (file: File, modelKey = 'all') => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClientV2.post('/batch', formData, { params: { model_key: modelKey }, headers: { 'Content-Type': 'multipart/form-data' } });
    return res.data as {
      model_key: string;
      total_rows: number;
      results: ({ row: number; predictions?: Record<string, 'Low' | 'Medium' | 'High'>; predicted_band?: 'Low' | 'Medium' | 'High' } | null)[];
      errors: { row: number; error: string }[];
      latency_ms: number;
    };
  },
};
