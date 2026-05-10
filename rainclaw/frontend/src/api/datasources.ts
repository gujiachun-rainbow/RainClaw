import { apiClient, ApiResponse } from './client';

export type DbType = 'MySQL' | 'PostgreSQL' | 'Oracle' | 'MongoDB' | 'SQL Server';

export interface Datasource {
  id: string;
  name: string;
  code: string;
  host: string;
  port: number;
  databaseName: string;
  username: string;
  password: string;
  dbType: DbType;
  createdAt: number;
  updatedAt: number;
}

export interface CreateDatasourceRequest {
  name: string;
  code: string;
  host: string;
  port: number;
  databaseName: string;
  username: string;
  password: string;
  dbType: DbType;
}

export interface UpdateDatasourceRequest {
  name?: string;
  code?: string;
  host?: string;
  port?: number;
  databaseName?: string;
  username?: string;
  password?: string;
  dbType?: DbType;
}

/** Convert frontend camelCase to backend snake_case */
function toSnakeCase(data: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
    result[snakeKey] = value;
  }
  return result;
}

/** Convert backend snake_case to frontend camelCase */
function toCamelCase(data: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    result[camelKey] = value;
  }
  return result;
}

export async function listDatasources(name?: string): Promise<Datasource[]> {
  const params = name ? { name } : undefined;
  const response = await apiClient.get<ApiResponse<Record<string, unknown>[]>>('/datasources', { params });
  return (response.data.data || []).map((item) => toCamelCase(item) as unknown as Datasource);
}

export async function createDatasource(data: CreateDatasourceRequest): Promise<Datasource> {
  const response = await apiClient.post<ApiResponse<Record<string, unknown>>>('/datasources', toSnakeCase(data as unknown as Record<string, unknown>));
  return toCamelCase(response.data.data) as unknown as Datasource;
}

export async function updateDatasource(id: string, data: UpdateDatasourceRequest): Promise<Datasource> {
  const response = await apiClient.put<ApiResponse<Record<string, unknown>>>(`/datasources/${id}`, toSnakeCase(data as unknown as Record<string, unknown>));
  return toCamelCase(response.data.data) as unknown as Datasource;
}

export async function deleteDatasource(id: string): Promise<void> {
  await apiClient.delete(`/datasources/${id}`);
}
