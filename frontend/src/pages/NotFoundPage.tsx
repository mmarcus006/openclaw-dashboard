/**
 * NotFoundPage — 404 page for invalid routes.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion } from 'lucide-react';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/common/Button';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';

export default function NotFoundPage(): React.ReactElement {
  const navigate = useNavigate();
  useDocumentTitle('Not Found');

  return (
    <Layout title="Not Found">
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
        <FileQuestion size={48} className="text-text-tertiary" />
        <h2 className="text-text-primary text-lg font-semibold">Page not found</h2>
        <p className="text-text-secondary text-sm max-w-sm">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Button variant="primary" size="md" onClick={() => navigate('/')}>
          Go home
        </Button>
      </div>
    </Layout>
  );
}
