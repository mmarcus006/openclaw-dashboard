/**
 * Sessions API — fetch session list and messages.
 */

import { apiClient } from './client';

export interface ContentBlock {
  type: string;
  text?: string | null;
  thinking?: string | null;
  id?: string | null;
  name?: string | null;
  arguments?: Record<string, unknown> | null;
  tool_call_id?: string | null;
  content?: string | unknown[] | null;
}

export interface SessionMessage {
  id: string;
  role: string;
  content: ContentBlock[];
  content_text: string | null;
  timestamp: string | null;
  parent_id: string | null;
}

export interface SessionSummary {
  session_id: string;
  updated_at: number;
  model: string | null;
  model_provider: string | null;
  label: string | null;
  spawned_by: string | null;
  total_tokens: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cache_read: number | null;
  message_count: number | null;
  session_file: string | null;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
  total: number;
  warning: string | null;
}

export interface SessionMessageListResponse {
  messages: SessionMessage[];
  total: number;
  has_more: boolean;
  skipped_lines: number;
  warning: string | null;
}

export const sessionsApi = {
  list: (agentId: string, offset = 0, limit = 20) =>
    apiClient.get<SessionListResponse>(
      `/api/agents/${encodeURIComponent(agentId)}/sessions?limit=${limit}&offset=${offset}`,
    ),

  getMessages: (sessionId: string, offset = 0, limit = 50, full = false) =>
    apiClient.get<SessionMessageListResponse>(
      `/api/sessions/${encodeURIComponent(sessionId)}/messages?limit=${limit}&offset=${offset}&full=${full}`,
    ),
};
