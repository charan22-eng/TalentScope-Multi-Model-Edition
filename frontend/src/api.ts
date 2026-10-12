import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export interface PredictionRequest {
  attendance: number;
  experience_years: number;
  training_hours: number;
  projects_completed: number;
  weekly_hours: number;
  prev_score: number;
  department: string;
  job_level: string;
}

export interface PredictionResponse {
  prediction: string;
  confidence: number;
  summary: string;
  votes: Record<string, number>;
  attribution: Record<string, number>;
  neighbours: Record<string, unknown>[];
  counterfactual_path: string[];
  is_flagged: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Interceptor to add auth token
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  login: async (username: string, password: string):Promise<LoginResponse> => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    const response = await axios.post(`${API_URL}/login`, params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  },
  predict: async (data: PredictionRequest): Promise<PredictionResponse> => {
    const response = await axios.post(`${API_URL}/predict`, data);
    return response.data;
  },
  getMetadata: async () => {
    const response = await axios.get(`${API_URL}/metadata`);
    return response.data;
  }
};
