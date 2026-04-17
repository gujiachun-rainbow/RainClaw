/**
 * Task Scheduler Service API.
 * Base URL: VITE_TASK_SERVICE_URL or /task-service (proxied in dev).
 */
import axios from 'axios';
import { getStoredToken } from './auth';

const TASK_SERVICE_BASE =
  (import.meta as any).env?.VITE_TASK_SERVICE_URL ?? '';

const taskClient = axios.create({
  baseURL: TASK_SERVICE_BASE || '/task-service',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

taskClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Task {
  id: string;
  name: string;
  prompt: string;
  schedule_desc: string;
  crontab: string;
  webhook?: string;
  webhook_ids?: string[];
  event_config: string[];
  model_config_id?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  /** 下次执行时间（展示时区），列表接口返回 */
  next_run?: string;
  total_runs?: number;
  success_runs?: number;
  success_rate?: string;
  recent_runs?: string[];
}

export interface TaskRun {
  id: string;
  task_id: string;
  status: string;
  chat_id?: string;
  start_time?: string;
  end_time?: string;
  result?: string;
  error?: string;
}

export interface TaskCreatePayload {
  name: string;
  prompt: string;
  schedule_desc: string;
  crontab?: string;
  webhook?: string;
  webhook_ids?: string[];
  event_config?: string[];
  model_config_id?: string;
  status?: string;
  user_id?: string;
}

export interface TaskUpdatePayload {
  name?: string;
  prompt?: string;
  schedule_desc?: string;
  crontab?: string;
  webhook?: string;
  webhook_ids?: string[];
  event_config?: string[];
  model_config_id?: string;
  status?: string;
  user_id?: string;
}

export async function listTasks(): Promise<Task[]> {
  const { data } = await taskClient.get<Task[]>('/tasks');
  return Array.isArray(data) ? data : [];
}

export async function getTask(id: string): Promise<Task> {
  const { data } = await taskClient.get<Task>(`/tasks/${id}`);
  return data;
}

export async function createTask(payload: TaskCreatePayload): Promise<Task> {
  const { data } = await taskClient.post<Task>('/tasks', payload);
  return data;
}

export async function updateTask(id: string, payload: TaskUpdatePayload): Promise<Task> {
  const { data } = await taskClient.put<Task>(`/tasks/${id}`, payload);
  return data;
}

export async function deleteTask(id: string): Promise<void> {
  await taskClient.delete(`/tasks/${id}`);
}

export async function verifyWebhook(webhookUrl: string, taskName: string): Promise<{ success: boolean; message: string }> {
  const { data } = await taskClient.post<{ success: boolean; message: string }>('/tasks/verify-webhook', {
    webhook_url: webhookUrl,
    task_name: taskName || '',
  });
  return data;
}

export async function validateSchedule(scheduleDesc: string, modelConfigId?: string): Promise<{ valid: boolean; crontab: string; next_run: string }> {
  const payload: Record<string, string> = { schedule_desc: scheduleDesc || '' };
  if (modelConfigId) payload.model_config_id = modelConfigId;
  const { data } = await taskClient.post<{ valid: boolean; crontab: string; next_run: string }>('/tasks/validate-schedule', payload);
  return data;
}

export interface TaskRunsPage {
  items: TaskRun[];
  total: number;
}

export async function listTaskRuns(
  taskId: string,
  page = 1,
  pageSize = 20
): Promise<TaskRunsPage> {
  const limit = Math.max(1, Math.min(200, pageSize));
  const offset = (Math.max(1, page) - 1) * limit;
  const { data } = await taskClient.get<{ items: TaskRun[]; total: number }>(
    `/tasks/${taskId}/runs`,
    { params: { limit, offset } }
  );
  return {
    items: Array.isArray(data?.items) ? data.items : [],
    total: typeof data?.total === 'number' ? data.total : 0,
  };
}

export async function listTaskRunsByOffset(
  taskId: string,
  offset = 0,
  limit = 20
): Promise<TaskRunsPage> {
  const { data } = await taskClient.get<{ items: TaskRun[]; total: number }>(
    `/tasks/${taskId}/runs`,
    { params: { limit: Math.min(200, limit), offset: Math.max(0, offset) } }
  );
  return {
    items: Array.isArray(data?.items) ? data.items : [],
    total: typeof data?.total === 'number' ? data.total : 0,
  };
}

export function isTaskServiceConfigured(): boolean {
  return !!((import.meta as any).env?.VITE_TASK_SERVICE_URL || '/task-service');
}
