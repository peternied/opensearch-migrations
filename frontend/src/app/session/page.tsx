'use client';

import { Suspense, useState } from 'react';
import SourceSelector from '@/component/connection/connection-source-selector';
import Connection from '@/component/connection/remote-connection';
import MetadataWorkflowControl from '@/component/metadata/selection';
import BackfillStatusDashboard from '@/component/backfill/status';
import RequestTimeline from '@/component/capture/request-timeline';
import {
  Box,
  Header,
  SpaceBetween,
  Wizard,
  WizardProps
} from '@cloudscape-design/components';
import SnapshotCreation from '@/component/snapshot/creation';
import MigrationSessionReviewPage from '@/component/session/review';
import DemoWrapper from '@/component/demoWrapper';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMigrationSessions } from '@/context/migration-session';
import CaptureProxiesOverview from '@/component/capture/captured-overview';

const steps: WizardProps.Step[] = [
  {
    title: 'Select Source',
    content: <SourceSelector />,
    isOptional: true
  },
  {
    title: 'Traffic Capture',
    content: <CaptureProxiesOverview />,
    isOptional: true
  },
  {
    title: 'Select Target',
    content: <Connection connectionType="target" />,
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
    content: <RequestTimeline proxies={[]} showReplayers={true} />,
    isOptional: true
  },
  {
    title: 'Review',
    content: <MigrationSessionReviewPage />
  }
];

function StepPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialStep = parseInt(searchParams.get('step') ?? '0', 10);

  const [activeStepIndex, setActiveStepIndex] = useState(
    isNaN(initialStep)
      ? 0
      : Math.min(Math.max(initialStep, 0), steps.length - 1)
  );

  const handleStepChange = ({
    detail
  }: {
    detail: { requestedStepIndex: number };
  }) => {
    const nextIndex = detail.requestedStepIndex;
    setActiveStepIndex(nextIndex);

    const currentParams = new URLSearchParams(window.location.search);
    currentParams.set('step', String(nextIndex));

    router.replace(`?${currentParams.toString()}`);
  };

  const { sessions } = useMigrationSessions();
  const sessionId = searchParams.get('id');
  const currentSession = sessions.find((s) => s.id == sessionId);

  return (
    <SpaceBetween size="xxl">
      <Header>Session: {currentSession?.name}</Header>
      <Wizard
        steps={steps}
        activeStepIndex={activeStepIndex}
        onNavigate={handleStepChange}
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
