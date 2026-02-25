/**
 * Config API — openclaw.json read/write.
 */

import { apiClient } from './client';
import type { ApiResponse } from './client';
import type {
  ConfigResponse,
  ConfigValidateResponse,
} from '@/types';

export type { ApiResponse };

export const configApi = {
  /** Get current openclaw.json (secrets redacted) */
  get: (): Promise<ApiResponse<ConfigResponse>> =>
    apiClient.get<ConfigResponse>('/api/config'),

  /**
   * Save updated config. Requires If-Match header.
   * Backend creates timestamped backup, writes atomically.
   * Returns ConfigResponse (not SaveResponse) — includes new config + etag.
   */
  save: (
    config: Record<string, unknown>,
    etag: string,
  ): Promise<ApiResponse<ConfigResponse>> =>
    apiClient.put<ConfigResponse>('/api/config', { config, etag }, etag),

  /** Validate JSON without saving */
  validate: (config: Record<string, unknown>): Promise<ApiResponse<ConfigValidateResponse>> =>
    apiClient.post<ConfigValidateResponse>('/api/config/validate', { config }),
};
