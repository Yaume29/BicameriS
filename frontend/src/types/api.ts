export type MessageRole = 'user' | 'assistant-left' | 'assistant-right' | 'corpus' | 'system' | 'osint';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  code?: string;
  sources?: string[];
  results?: OsintResult[];
}

export interface OsintResult {
  site: string;
  url: string;
  status: 'found' | 'not_found' | 'error';
}

export type AppMode = 'chat' | 'research' | 'code' | 'osint';

export interface SpecialistStatus {
  is_active: boolean;
  mode: string | null;
  memory_sleeping: boolean;
  session_id: string | null;
  sessions_count: number;
}

export interface ProcessRequest {
  input: string;
  context: Record<string, unknown>;
}

export interface ProcessResponse {
  status: 'ok' | 'error';
  mode: string;
  result?: unknown;
  message?: string;
}

export interface StreamEvent {
  type: 'thinking' | 'message' | 'status' | 'error' | 'complete';
  role?: MessageRole;
  content: string;
  session_id?: string;
}

export interface ModeChangeRequest {
  mode: AppMode;
  capabilities?: Record<string, boolean>;
}

export interface ModeChangeResponse {
  status: 'ok' | 'error';
  mode: string;
  message?: string;
}

export const MODE_COLORS: Record<AppMode, { bg: string; border: string; label: string }> = {
  chat: { bg: 'bg-cyan-600', border: 'border-cyan-500', label: '🧠' },
  research: { bg: 'bg-purple-600', border: 'border-purple-500', label: '🔬' },
  code: { bg: 'bg-green-600', border: 'border-green-500', label: '💻' },
  osint: { bg: 'bg-red-600', border: 'border-red-500', label: '🕵️' },
};
