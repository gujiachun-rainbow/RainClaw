import { apiClient, type ApiResponse } from './client';

export interface LarkBindingStatus {
  bound: boolean;
  platform?: string;
  platform_user_id?: string;
  science_user_id?: string;
  status?: string;
  updated_at?: number;
}

export interface BindLarkRequest {
  lark_user_id: string;
  lark_union_id?: string;
}

export interface IMSystemSettings {
  im_enabled: boolean;
  im_response_timeout: number;
  im_max_message_length: number;
  lark_enabled: boolean;
  lark_app_id: string;
  has_lark_app_secret: boolean;
  lark_app_secret_masked: string;
  im_progress_mode: 'text_multi' | 'card_entity';
  im_progress_detail_level: 'compact' | 'detailed';
  im_progress_interval_ms: number;
  im_realtime_events: Array<'plan_update' | 'planning_message' | 'tool_call' | 'tool_result' | 'error'>;
}

export interface UpdateIMSystemSettingsRequest {
  im_enabled?: boolean;
  im_response_timeout?: number;
  im_max_message_length?: number;
  lark_enabled?: boolean;
  lark_app_id?: string;
  lark_app_secret?: string;
  im_progress_mode?: 'text_multi' | 'card_entity';
  im_progress_detail_level?: 'compact' | 'detailed';
  im_progress_interval_ms?: number;
  im_realtime_events?: Array<'plan_update' | 'planning_message' | 'tool_call' | 'tool_result' | 'error'>;
}

export async function getLarkBindingStatus(): Promise<LarkBindingStatus> {
  const response = await apiClient.get<ApiResponse<LarkBindingStatus>>('/im/bind/lark/status');
  return response.data.data;
}

export async function bindLarkAccount(payload: BindLarkRequest): Promise<LarkBindingStatus> {
  const response = await apiClient.post<ApiResponse<LarkBindingStatus>>('/im/bind/lark', payload);
  return response.data.data;
}

export async function unbindLarkAccount(): Promise<{ removed: boolean }> {
  const response = await apiClient.delete<ApiResponse<{ removed: boolean }>>('/im/bind/lark');
  return response.data.data;
}

export async function getIMSystemSettings(): Promise<IMSystemSettings> {
  const response = await apiClient.get<ApiResponse<IMSystemSettings>>('/im/settings');
  return response.data.data;
}

export async function updateIMSystemSettings(payload: UpdateIMSystemSettingsRequest): Promise<IMSystemSettings> {
  const response = await apiClient.put<ApiResponse<IMSystemSettings>>('/im/settings', payload);
  return response.data.data;
}




