import { apiClient, type ApiResponse } from './client';

export interface MemoryData {
  content: string;
}

export interface AdminMemoryEntry {
  id: string;
  scope: string[] | null;
  category: string;
  content: string;
  created_by: string;
  created_at: number;
  updated_at: number;
}

export interface AdminMemoryListData {
  entries: AdminMemoryEntry[];
}

export interface AdminMemoryEntryData {
  entry: AdminMemoryEntry;
}

export async function getMemory(): Promise<MemoryData> {
  const response = await apiClient.get<ApiResponse<MemoryData>>('/memory');
  return response.data.data;
}

export async function updateMemory(content: string): Promise<MemoryData> {
  const response = await apiClient.put<ApiResponse<MemoryData>>('/memory', { content });
  return response.data.data;
}

// Admin global memory CRUD
export async function listAdminMemory(): Promise<AdminMemoryListData> {
  const response = await apiClient.get<ApiResponse<AdminMemoryListData>>('/memory/admin');
  return response.data.data;
}

export async function createAdminMemory(params: {
  scope?: string[] | null;
  category: string;
  content: string;
}): Promise<AdminMemoryEntryData> {
  const response = await apiClient.post<ApiResponse<AdminMemoryEntryData>>('/memory/admin', params);
  return response.data.data;
}

export async function updateAdminMemory(
  entryId: string,
  params: {
    scope?: string[] | null;
    category?: string;
    content?: string;
  },
): Promise<AdminMemoryEntryData> {
  const response = await apiClient.put<ApiResponse<AdminMemoryEntryData>>(`/memory/admin/${entryId}`, params);
  return response.data.data;
}

export async function deleteAdminMemory(entryId: string): Promise<void> {
  await apiClient.delete<ApiResponse<any>>(`/memory/admin/${entryId}`);
}
