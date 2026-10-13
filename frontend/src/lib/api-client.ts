import axios from 'axios';
import type { components } from './api';

export type EmployeeFeatures = components['schemas']['EmployeeFeatures'];
export type PredictResponse = components['schemas']['PredictResponse'];
export type ExplainResponse = components['schemas']['ExplainResponse'];

export interface BatchPredictResponse {
  results: (PredictResponse | null)[];
  errors: ({ row: number; error: string } | null)[];
}

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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
