import axios from 'axios';
import type { components } from './api';

import { ensureAuthToken } from './auth-bootstrap';

export type EmployeeFeatures = components['schemas']['EmployeeFeatures'];
export type PredictResponse = components['schemas']['PredictResponse'];
export type ExplainResponse = components['schemas']['ExplainResponse'];

export interface BatchPredictResponse {
  results: (PredictResponse | null)[];
  errors: ({ row: number; error: string } | null)[];
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_ORIGIN || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(async (config) => {
  let token = localStorage.getItem('token');
  if (!token) {
    token = await ensureAuthToken();
  }
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
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
        return apiClient(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);

export const predict = async (features: EmployeeFeatures): Promise<PredictResponse> => {
  const { data } = await apiClient.post<PredictResponse>('/predict', features);
  return data;
};

export const explain = async (features: EmployeeFeatures, k: number = 5): Promise<ExplainResponse> => {
  const { data } = await apiClient.post<ExplainResponse>(`/explain?k=${k}`, features);
  return data;
};

export const batchPredict = async (file: File): Promise<BatchPredictResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<BatchPredictResponse>('/batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};
