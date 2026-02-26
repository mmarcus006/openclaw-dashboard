/**
 * Toast store — notification queue.
 */

import { create } from 'zustand';
import type { Toast, ToastVariant } from '@/types';

interface ToastState {
  toasts: Toast[];
  addToast: (variant: ToastVariant, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

const MAX_TOASTS = 3;
let toastCounter = 0;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (variant: ToastVariant, message: string, duration = 5000) => {
    const id = `toast-${++toastCounter}`;
    set((state) => {
      const next = [...state.toasts, { id, variant, message, duration }];
      return { toasts: next.slice(-MAX_TOASTS) };
    });
  },

  removeToast: (id: string) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  clearAll: () => set({ toasts: [] }),
}));

/** Convenience helpers — call these from API error handlers */
export function toastSuccess(message: string): void {
  useToastStore.getState().addToast('success', message);
}

export function toastError(message: string): void {
  useToastStore.getState().addToast('error', message, 6000);
}

export function toastInfo(message: string): void {
  useToastStore.getState().addToast('info', message);
}

export function toastWarning(message: string): void {
  useToastStore.getState().addToast('warning', message, 5000);
}
