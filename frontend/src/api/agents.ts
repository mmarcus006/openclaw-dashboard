/**
 * Agent API — all agent-related HTTP calls.
 */

import { apiClient } from './client';
import type { ApiResponse } from './client';
import type {
  AgentListResponse,
  AgentDetailResponse,
  FileContentResponse,
  SaveResponse,
} from '@/types';

export type { ApiResponse };

export const agentsApi = {
  /** List all agents */
  list: (): Promise<ApiResponse<AgentListResponse>> =>
    apiClient.get<AgentListResponse>('/api/agents'),

  /** Get agent detail including workspace files */
  get: (agentId: string): Promise<ApiResponse<AgentDetailResponse>> =>
    apiClient.get<AgentDetailResponse>(`/api/agents/${encodeURIComponent(agentId)}`),

  /**
   * Get file content. Returns ETag in response for concurrency control.
   * File path sent as query param (R1 — avoids URL routing issues with slashes).
   */
  getFile: (agentId: string, filePath: string): Promise<ApiResponse<FileContentResponse>> =>
    apiClient.get<FileContentResponse>(
      `/api/agents/${encodeURIComponent(agentId)}/files?path=${encodeURIComponent(filePath)}`,
    ),

  /**
   * Save file content. Requires If-Match header for concurrency control (R7).
   * Throws ApiError with code CONFLICT (409) if file changed since GET.
   */
  saveFile: (
    agentId: string,
    filePath: string,
    content: string,
    etag: string,
  ): Promise<ApiResponse<SaveResponse>> =>
    apiClient.put<SaveResponse>(
      `/api/agents/${encodeURIComponent(agentId)}/files?path=${encodeURIComponent(filePath)}`,
      { content },
      etag,
    ),
};
