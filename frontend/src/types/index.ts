/**
 * Type re-exports and manual supplementary types.
 *
 * Auto-generated types come from `generated.ts` (via `make types`).
 * Manual types below cover WebSocket protocol, error envelopes, and
 * UI-only state — none of which appear in the OpenAPI spec.
 */

import type { components } from './generated';

// ---------------------------------------------------------------------------
// Re-export Pydantic-derived types from OpenAPI (schema components)
// ---------------------------------------------------------------------------

export type AgentFileInfo = components['schemas']['AgentFileInfo'];
export type AgentSummary = components['schemas']['AgentSummary'];
export type AgentDetailResponse = components['schemas']['AgentDetailResponse'];
export type AgentListResponse = components['schemas']['AgentListResponse'];
export type FileContentResponse = components['schemas']['FileContentResponse'];
export type SaveResponse = components['schemas']['SaveResponse'];
export type HealthResponse = components['schemas']['HealthResponse'];
export type ConfigResponse = components['schemas']['ConfigResponse'];
export type ConfigValidateResponse = components['schemas']['ConfigValidateResponse'];
export type ConfigWriteRequest = components['schemas']['ConfigWriteRequest'];
export type GatewayAction = components['schemas']['GatewayAction'];
export type GatewayStatusResponse = components['schemas']['GatewayStatusResponse'];
export type CommandResponse = components['schemas']['CommandResponse'];
export type GatewayCommandEntry = components['schemas']['GatewayCommandEntry'];
export type GatewayHistoryResponse = components['schemas']['GatewayHistoryResponse'];
export type CronJobEntry = components['schemas']['CronJobEntry'];
export type CronJobListResponse = components['schemas']['CronJobListResponse'];

// ---------------------------------------------------------------------------
// Manual: typed subsystems map (backend returns dict, we know the shape)
// ---------------------------------------------------------------------------

export interface HealthSubsystems {
  config: boolean;
  workspaces: boolean;
  gateway_cli: boolean;
  sessions: boolean;
}

// ---------------------------------------------------------------------------
// Manual: Error envelope (used by client.ts — not a response model in OpenAPI)
// ---------------------------------------------------------------------------

export interface ErrorEnvelope {
  code: string;
  message: string;
  detail: Record<string, unknown> | null;
  timestamp: string;
}

export interface ErrorResponse {
  error: ErrorEnvelope;
}

// ---------------------------------------------------------------------------
// Manual: WebSocket protocol types (R11 — not in OpenAPI spec)
// ---------------------------------------------------------------------------

export type WsMessageType = 'gateway_status' | 'file_changed' | 'error' | 'ping';

export interface WsGatewayStatusPayload {
  running: boolean;
  pid: number | null;
  uptime: string | null;
  error: string | null;
}

export interface WsFileChangedPayload {
  agent_id: string | null;
  path: string;
  name: string;
  change: 'added' | 'modified' | 'deleted';
}

export interface WsErrorPayload {
  message: string;
}

export interface WsMessage {
  type: WsMessageType;
  timestamp: string;
  payload: WsGatewayStatusPayload | WsFileChangedPayload | WsErrorPayload | Record<string, never>;
}

// ---------------------------------------------------------------------------
// Manual: UI-only types (not from API)
// ---------------------------------------------------------------------------

export type ToastVariant = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  variant: ToastVariant;
  message: string;
  duration?: number;
}

export interface EditorFile {
  agentId: string;
  path: string;
  content: string;
  originalContent: string;  // Needed for accurate dirty detection
  dirty: boolean;
  etag: string;
  language: string;
}

export type WsConnectionState = 'connected' | 'connecting' | 'disconnected';
