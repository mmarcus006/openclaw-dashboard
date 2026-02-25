/**
 * Gateway API — openclaw gateway controls.
 */

import { apiClient } from './client';
import type { ApiResponse } from './client';
import type {
  GatewayStatusResponse,
  CommandResponse,
  GatewayAction,
} from '@/types';

export type { ApiResponse };

export const gatewayApi = {
  /** Get current gateway status */
  status: (): Promise<ApiResponse<GatewayStatusResponse>> =>
    apiClient.get<GatewayStatusResponse>('/api/gateway/status'),

  /**
   * Perform a gateway action (start | stop | restart).
   * Backend validates action against enum (R6).
   */
  action: (action: GatewayAction): Promise<ApiResponse<CommandResponse>> =>
    apiClient.post<CommandResponse>(`/api/gateway/${action}`),
};
