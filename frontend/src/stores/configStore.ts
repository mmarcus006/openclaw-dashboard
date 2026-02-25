/**
 * Config store — openclaw.json content, dirty flag, etag.
 */

import { create } from 'zustand';
import { configApi } from '@/api/config';
import type { ConfigValidateResponse } from '@/types';

interface ConfigState {
  content: string;          // JSON string (for Monaco editor)
  originalContent: string;  // Last saved version (for dirty detection)
  etag: string;
  path: string;
  dirty: boolean;
  loading: boolean;
  saving: boolean;
  error: string | null;
  validation: ConfigValidateResponse | null;
  conflictEtag: string | null;

  fetchConfig: () => Promise<void>;
  updateContent: (content: string) => void;
  saveConfig: () => Promise<boolean>;
  validateConfig: () => Promise<void>;
  clearConflict: () => void;
}

export const useConfigStore = create<ConfigState>((set, get) => ({
  content: '',
  originalContent: '',
  etag: '',
  path: '',
  dirty: false,
  loading: false,
  saving: false,
  error: null,
  validation: null,
  conflictEtag: null,

  fetchConfig: async () => {
    set({ loading: true, error: null, conflictEtag: null });
    try {
      const { data } = await configApi.get();
      const jsonStr = JSON.stringify(data.config, null, 2);
      set({
        content: jsonStr,
        originalContent: jsonStr,
        etag: data.etag,
        path: data.path,
        dirty: false,
        loading: false,
      });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  updateContent: (content: string) => {
    const { originalContent } = get();
    set({ content, dirty: content !== originalContent });
  },

  saveConfig: async () => {
    const { content, etag } = get();
    set({ saving: true, error: null });

    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(content) as Record<string, unknown>;
    } catch {
      set({ saving: false, error: 'Invalid JSON — fix syntax errors before saving' });
      return false;
    }

    try {
      await configApi.save(parsed, etag);
      // Refetch to get new etag and any server-side normalisation
      await get().fetchConfig();
      set({ saving: false });
      return true;
    } catch (e) {
      const error = e as { code?: string; message?: string };
      if (error.code === 'CONFLICT') {
        set({ saving: false, conflictEtag: error.message ?? null, error: 'CONFLICT' });
      } else {
        set({ saving: false, error: String(e) });
      }
      return false;
    }
  },

  validateConfig: async () => {
    const { content } = get();
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(content) as Record<string, unknown>;
    } catch {
      set({
        validation: {
          valid: false,
          errors: ['Invalid JSON syntax'],
          warnings: [],
        },
      });
      return;
    }
    try {
      const { data } = await configApi.validate(parsed);
      set({ validation: data });
    } catch (e) {
      set({ error: String(e) });
    }
  },

  clearConflict: () => set({ conflictEtag: null, error: null }),
}));
