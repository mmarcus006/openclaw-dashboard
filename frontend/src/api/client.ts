/**
 * Fetch wrapper — all API calls go through here.
 * Parses the error envelope on non-2xx responses.
 * Handles ETag flow.
 * Dispatches network errors to toast store.
 */

import type { ErrorEnvelope } from '@/types';

export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly detail: Record<string, unknown> | null;

  constructor(envelope: ErrorEnvelope, status: number) {
    super(envelope.message);
    this.name = 'ApiError';
    this.code = envelope.code;
    this.status = status;
    this.detail = envelope.detail;
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
  /** ETag value to send as If-Match header on write operations */
  ifMatch?: string;
}

export interface ApiResponse<T> {
  data: T;
  /** ETag from response headers (on GET responses) */
  etag?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
  const { method = 'GET', body, headers = {}, ifMatch } = options;

  const reqHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (ifMatch !== undefined) {
    reqHeaders['If-Match'] = ifMatch;
  }

  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: reqHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new NetworkError('Backend unreachable — is the dashboard server running?');
  }

  const etag = response.headers.get('ETag') ?? undefined;

  if (!response.ok) {
    let envelope: ErrorEnvelope;
    try {
      const json = await response.json() as { error: ErrorEnvelope };
      envelope = json.error;
    } catch {
      envelope = {
        code: 'UNKNOWN_ERROR',
        message: `HTTP ${response.status}: ${response.statusText}`,
        detail: null,
        timestamp: new Date().toISOString(),
      };
    }
    throw new ApiError(envelope, response.status);
  }

  const data = await response.json() as T;
  return { data, etag };
}

export const apiClient = {
  get: <T>(path: string, headers?: Record<string, string>): Promise<ApiResponse<T>> =>
    request<T>(path, { method: 'GET', headers }),

  post: <T>(path: string, body?: unknown): Promise<ApiResponse<T>> =>
    request<T>(path, { method: 'POST', body }),

  put: <T>(path: string, body?: unknown, ifMatch?: string): Promise<ApiResponse<T>> =>
    request<T>(path, { method: 'PUT', body, ifMatch }),

  delete: <T>(path: string): Promise<ApiResponse<T>> =>
    request<T>(path, { method: 'DELETE' }),
};
