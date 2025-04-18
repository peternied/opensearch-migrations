'use client';

import { Suspense } from 'react';
import Header from '@cloudscape-design/components/header';
import SourceSelector from '@/component/source-selector';
import TargetConnection from '@/component/connection/target';
import MetadataWorkflowControl from '@/component/metadata/selection';
import BackfillStatusDashboard from '@/component/backfill/status';
import RequestPlaybackTimeline from '@/component/playback';
import { Wizard } from '@cloudscape-design/components';
import SnapshotCreation from '@/component/snapshot/creation';
import MigrationSessionReviewPage from '@/component/session/review';

function StepPageContent() {
  return (
    <Wizard
      steps={[
        {
          title: 'Select Source',
          content: <SourceSelector />,
          isOptional: true
        },
        {
          title: 'Traffic Capture',
          content: <RequestPlaybackTimeline />,
          isOptional: true
        },
        {
          title: 'Select Target',
          content: <TargetConnection />,
          isOptional: true
        },
        {
          title: 'Create Snapshot',
          content: <SnapshotCreation />,
          isOptional: true
        },
        {
          title: 'Metadata',
          content: <MetadataWorkflowControl />,
          isOptional: true
        },
        {
          title: 'Backfill',
          content: <BackfillStatusDashboard />,
          isOptional: true
        },
        {
          title: 'Traffic Replay',
          content: <RequestPlaybackTimeline />,
          isOptional: true
        },
        {
          title: 'Review',
          content: <MigrationSessionReviewPage />
        }
      ]}
      submitButtonText="Mark Complete"
      allowSkipTo
    ></Wizard>
  );
}

export default function StepPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <StepPageContent />
    </Suspense>
  );
}
