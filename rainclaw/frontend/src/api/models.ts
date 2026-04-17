import { apiClient, ApiResponse } from './client';

export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  base_url?: string;
  api_key?: string;
  model_name: string;
  context_window?: number | null;
  is_system: boolean;
  user_id?: string;
  is_active: boolean;
  created_at: number;
  updated_at: number;
}

export interface CreateModelRequest {
  name: string;
  provider: string;
  base_url?: string;
  api_key?: string;
  model_name: string;
  context_window?: number | null;
}

export interface UpdateModelRequest {
  name?: string;
  base_url?: string;
  api_key?: string;
  model_name?: string;
  context_window?: number | null;
  is_active?: boolean;
}

export async function listModels(): Promise<ModelConfig[]> {
  const response = await apiClient.get<ApiResponse<ModelConfig[]>>('/models');
  return response.data.data;
}

export async function createModel(data: CreateModelRequest): Promise<ModelConfig> {
  const response = await apiClient.post<ApiResponse<ModelConfig>>('/models', data);
  return response.data.data;
}

export async function updateModel(id: string, data: UpdateModelRequest): Promise<void> {
  await apiClient.put(`/models/${id}`, data);
}

export async function deleteModel(id: string): Promise<void> {
  await apiClient.delete(`/models/${id}`);
}

export async function detectContextWindow(data: { provider: string; base_url?: string; api_key?: string; model_name: string; model_id?: string }): Promise<number> {
  const response = await apiClient.post<ApiResponse<{ context_window: number }>>('/models/detect-context-window', data);
  return response.data.data.context_window;
}
