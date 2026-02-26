/**
 * ConfirmDialog — "Are you sure?" modal wrapping the existing Modal component.
 */

import React from 'react';
import { Modal } from './Modal';

interface ConfirmDialogProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'warning' | 'default';
}

export function ConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  title = 'Confirm',
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
}: ConfirmDialogProps): React.ReactElement {
  const confirmClasses =
    variant === 'danger'
      ? 'bg-danger hover:bg-danger/80 text-white'
      : variant === 'warning'
      ? 'bg-warning hover:bg-warning/80 text-text-inverse'
      : 'bg-accent hover:bg-accent-hover text-white';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
      footer={
        <>
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary bg-bg-hover rounded-md transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${confirmClasses}`}
          >
            {confirmLabel}
          </button>
        </>
      }
    >
      <p className="text-text-secondary text-sm">{message}</p>
    </Modal>
  );
}
