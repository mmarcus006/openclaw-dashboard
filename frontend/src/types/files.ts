/**
 * Manual types for file browsing API.
 * These will eventually be replaced by generated types from OpenAPI.
 */

export interface FileEntry {
  name: string;
  path: string;
  size: number;
  mtime: number;
  is_binary: boolean;
  is_directory: boolean;
}

export interface FileListResponse {
  files: FileEntry[];
  total: number;
  truncated: boolean;
}
