import axios from 'axios';

export interface EmployeeFeatures {
  attendance: number;
  experience_years: number;
  training_hours: number;
  projects_completed: number;
  weekly_hours: number;
  prev_score: number;
  department: string;
  job_level: string;
}

export interface ModelPrediction {
  model_key: string;
  model_name?: string;
  prediction_set: ('Low' | 'Medium' | 'High')[];
  top_class: 'Low' | 'Medium' | 'High';
  probabilities: {
    Low: number;
    Medium: number;
    High: number;
  };
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
}

export interface ExplainResponse {
  model_key: string;
  explanation_type: 'native' | 'partial' | 'model_agnostic' | 'similar_cases';
  summary_hr: string;
  summary_ds: string;
  native_explanation?: {
    type?: string;
    coefficients?: Record<string, number>;
    odds_ratios?: Record<string, number>;
    feature_importances?: Record<string, number>;
    top_decision_rules?: string[];
    [key: string]: unknown;
  };
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
  }[];
}

export interface LeaderboardModel {
  key: string;
  name: string;
  family: string;
  macro_f1: number;
  macro_f1_ci_low: number;
  macro_f1_ci_high: number;
  accuracy: number;
  qwk: number;
  balanced_accuracy?: number;
  brier_score?: number;
  ece?: number;
  inference_latency_p95_ms?: number;
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
    confidence: 'high' | 'medium' | 'low';
    decision_strength: 'clear' | 'marginal' | 'none';
  };
  claims: {
    statement: string;
    fact_ids: string[];
  }[];
  trade_offs: string[];
  caveats: string[];
  why_not: Record<string, string>;
  validation: {
    passed: boolean;
    errors: string[];
    source: 'llm' | 'template_fallback';
    checks_evaluated: number;
  };
  evidence_packet_hash: string;
}

const API_V2_BASE = 'http://localhost:8000/api/v2';

export const apiClientV2 = axios.create({
  baseURL: API_V2_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClientV2.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const apiV2 = {
  getModels: async () => {
    const res = await apiClientV2.get('/models');
    return res.data;
  },

  predictSingle: async (modelKey: string, features: EmployeeFeatures): Promise<ModelPrediction> => {
    const res = await apiClientV2.post('/predict', {
      model_key: modelKey,
      ...features,
    });
    return res.data;
  },

  predictAll: async (features: EmployeeFeatures): Promise<PredictAllResponse> => {
    const res = await apiClientV2.post('/predict/all', features);
    return res.data;
  },

  explain: async (modelKey: string, features: EmployeeFeatures, k = 5): Promise<ExplainResponse> => {
    const res = await apiClientV2.post('/explain', {
      model_key: modelKey,
      k,
      ...features,
    });
    return res.data;
  },

  getCompare: async (topic: string) => {
    const res = await apiClientV2.get(`/compare/${topic}`);
    return res.data;
  },

  postMCDA: async (weights: Record<string, number>, profile = 'Custom'): Promise<MCDAResult> => {
    const res = await apiClientV2.post('/compare/mcda', {
      weights,
      profile,
    });
    return res.data;
  },

  getSurface: async (modelKey: string, resolution = 40) => {
    const res = await apiClientV2.get('/viz/surface', {
      params: { model: modelKey, resolution },
    });
    return res.data;
  },

  getPCA: async () => {
    const res = await apiClientV2.get('/viz/pca');
    return res.data;
  },

  getLLMHealth: async () => {
    const res = await apiClientV2.get('/llm/health');
    return res.data;
  },

  getLLMModels: async () => {
    const res = await apiClientV2.get('/llm/models');
    return res.data;
  },

  postLLMVerdict: async (payload: {
    mode?: string;
    profile?: string;
    audience?: string;
    rejected_model?: string;
  }): Promise<LLMVerdictResponse> => {
    const res = await apiClientV2.post('/llm/verdict', payload);
    return res.data;
  },
};
