import { apiClient, type ApiResponse } from './client';

export interface MemoryData {
  content: string;
}

export async function getMemory(): Promise<MemoryData> {
  const response = await apiClient.get<ApiResponse<MemoryData>>('/memory');
  return response.data.data;
}

export async function updateMemory(content: string): Promise<MemoryData> {
  const response = await apiClient.put<ApiResponse<MemoryData>>('/memory', { content });
  return response.data.data;
}
