/**
 * useDocumentTitle — sets document.title to `${title} — OpenClaw`.
 */

import { useEffect } from 'react';

export function useDocumentTitle(title: string): void {
  useEffect(() => {
    document.title = `${title} — OpenClaw`;
    return () => { document.title = 'OpenClaw'; };
  }, [title]);
}
