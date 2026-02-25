/**
 * Editor store — current file, content, dirty flag, etag.
 * Single-file editor (MVP — no tabs per R8).
 */

import { create } from 'zustand';
import { agentsApi } from '@/api/agents';
import type { EditorFile } from '@/types';

interface EditorState {
  currentFile: EditorFile | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  conflictEtag: string | null;  // Set to current server ETag on 409 conflict

  loadFile: (agentId: string, filePath: string) => Promise<void>;
  updateContent: (content: string) => void;
  saveFile: () => Promise<boolean>;
  /** Discard edits and revert content to the last-loaded server version. */
  discardChanges: () => void;
  /**
   * Keep local edits after a conflict: update the stored ETag to the server's
   * current value so the next saveFile() will use the correct If-Match header.
   */
  keepMyChanges: () => void;
  clearConflict: () => void;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  currentFile: null,
  loading: false,
  saving: false,
  error: null,
  conflictEtag: null,

  loadFile: async (agentId: string, filePath: string) => {
    set({ loading: true, error: null, conflictEtag: null });
    try {
      const { data, etag } = await agentsApi.getFile(agentId, filePath);
      set({
        currentFile: {
          agentId,
          path: data.path,
          content: data.content,
          originalContent: data.content,
          dirty: false,
          etag: etag ?? '',
          language: data.language,
        },
        loading: false,
      });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },

  updateContent: (content: string) => {
    const { currentFile } = get();
    if (!currentFile) return;
    set({
      currentFile: { ...currentFile, content, dirty: content !== currentFile.originalContent },
    });
  },

  saveFile: async () => {
    const { currentFile } = get();
    if (!currentFile || !currentFile.dirty) return true;

    set({ saving: true, error: null });
    try {
      const { data, etag } = await agentsApi.saveFile(
        currentFile.agentId,
        currentFile.path,
        currentFile.content,
        currentFile.etag,
      );
      set({
        currentFile: {
          ...currentFile,
          originalContent: currentFile.content,
          dirty: false,
          etag: etag ?? data.etag,
        },
        saving: false,
      });
      return true;
    } catch (e) {
      const error = e as { code?: string; message?: string; detail?: Record<string, string> | null };
      if (error.code === 'CONFLICT') {
        // 409 — file changed externally.
        // The server returns the current ETag in error.detail.current_etag.
        // Store it so keepMyChanges() can arm the next save with the correct If-Match.
        const serverEtag = error.detail?.current_etag ?? null;
        set({ saving: false, conflictEtag: serverEtag, error: 'CONFLICT' });
      } else {
        set({ saving: false, error: String(e) });
      }
      return false;
    }
  },

  discardChanges: () => {
    const { currentFile } = get();
    if (!currentFile) return;
    // Revert both content and dirty flag to the last-loaded server state.
    set({
      currentFile: {
        ...currentFile,
        content: currentFile.originalContent,
        dirty: false,
      },
      conflictEtag: null,
      error: null,
    });
  },

  keepMyChanges: () => {
    // Update the stored ETag to the server's current value so the next
    // saveFile() sends the correct If-Match header (force-save semantics).
    const { currentFile, conflictEtag } = get();
    if (!currentFile || !conflictEtag) {
      set({ conflictEtag: null, error: null });
      return;
    }
    set({
      currentFile: { ...currentFile, etag: conflictEtag },
      conflictEtag: null,
      error: null,
    });
  },

  clearConflict: () => set({ conflictEtag: null, error: null }),
}));
