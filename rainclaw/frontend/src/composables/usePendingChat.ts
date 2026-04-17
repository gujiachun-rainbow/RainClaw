import type { FileInfo } from '../api/file';

interface PendingChatData {
  message: string;
  files: FileInfo[];
  mode?: string;
  selectedModelId?: string | null;
}

let _pending: PendingChatData | null = null;

export function setPendingChat(data: PendingChatData) {
  _pending = data;
}

export function consumePendingChat(): PendingChatData | null {
  const data = _pending;
  _pending = null;
  return data;
}
