'use client';

import { Suspense } from 'react';
import SourceSelector from '@/component/source-selector';
import TargetConnection from '@/component/connection/target';
import MetadataWorkflowControl from '@/component/metadata/selection';
import BackfillStatusDashboard from '@/component/backfill/status';
import RequestPlaybackTimeline from '@/component/playback';
import { Box, SpaceBetween, Wizard } from '@cloudscape-design/components';
import SnapshotCreation from '@/component/snapshot/creation';
import MigrationSessionReviewPage from '@/component/session/review';
import DemoWrapper from '@/component/demoWrapper';

function StepPageContent() {
  return (
    <SpaceBetween size="xxl">
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
      <DemoWrapper>
        <Box>
          Steps marked <i>Optional</i> is only for ease of navigation through
          this demo experience. These labels and &apos;skip&apos; options will
          not be present in the final version.
        </Box>
      </DemoWrapper>
    </SpaceBetween>
  );
}

export default function StepPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <StepPageContent />
    </Suspense>
  );
}
