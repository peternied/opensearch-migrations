'use client';

import { Spinner } from '@cloudscape-design/components';
import { Suspense } from 'react';
import MigrationSessionReviewPage from '@/components/session/review';

export default function MigrationDashboardPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <MigrationSessionReviewPage />
    </Suspense>
  );
}
