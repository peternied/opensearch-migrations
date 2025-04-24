'use client';

import { Suspense, useState } from 'react';
import SourceSelector from '@/components/connection/connection-source-selector';
import Connection from '@/components/connection/remote-connection';
import BackfillStatusDashboard from '@/components/backfill/status';
import RequestTimeline from '@/components/capture/request-timeline';
import {
  Box,
  Button,
  Flashbar,
  FlashbarProps,
  Header,
  Link,
  SpaceBetween,
  Wizard,
  WizardProps
} from '@cloudscape-design/components';
import SnapshotCreation from '@/components/snapshot/creation';
import MigrationSessionReviewPage from '@/components/session/review';
import DemoWrapper from '@/components/demoWrapper';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  SessionWorkflow,
  useMigrationSessions
} from '@/context/migration-session';
import CaptureProxiesOverview from '@/components/capture/captured-overview';
import MetadataEvaluationAndMigration from '@/components/metadata/evaulation';

type StepId =
  | 'select-source'
  | 'capture-traffic'
  | 'select-target'
  | 'create-snapshot'
  | 'metadata'
  | 'backfill'
  | 'replay-traffic'
  | 'review';

interface SessionStep extends WizardProps.Step {
  validWorkflows: SessionWorkflow[];
  requiredSteps: StepId[];
  stepId: StepId;
}

const stepDefinitions: SessionStep[] = [
  {
    title: 'Select Source',
    content: <SourceSelector />,
    stepId: 'select-source',
    requiredSteps: [],
    validWorkflows: ['backfill', 'freeform', 'full']
  },
  {
    title: 'Capture Traffic',
    content: <CaptureProxiesOverview />,
    stepId: 'capture-traffic',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'replay']
  },
  {
    title: 'Select Target',
    content: <Connection connectionType="target" />,
    stepId: 'select-target',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'replay', 'backfill']
  },
  {
    title: 'Create Snapshot',
    content: <SnapshotCreation />,
    stepId: 'create-snapshot',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'backfill']
  },
  {
    title: 'Metadata',
    content: <MetadataEvaluationAndMigration />,
    stepId: 'metadata',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'backfill']
  },
  {
    title: 'Backfill',
    content: <BackfillStatusDashboard />,
    stepId: 'backfill',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'backfill']
  },
  {
    title: 'Traffic Replay',
    content: <RequestTimeline proxies={[]} showReplayers={true} />,
    stepId: 'replay-traffic',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'replay']
  },
  {
    title: 'Review Finished Migration',
    content: <MigrationSessionReviewPage />,
    stepId: 'review',
    requiredSteps: [],
    validWorkflows: ['freeform', 'full', 'replay', 'backfill']
  }
];

function createSteps(sessionWorkflow: SessionWorkflow) {
  const filteredSteps = stepDefinitions.filter((s) =>
    s.validWorkflows.includes(sessionWorkflow)
  );
  const steps = filteredSteps.map((s) => {
    if (sessionWorkflow === 'freeform') {
      s.isOptional = true;
    }
    return s;
  });
  console.log('Steps: ' + steps);
  return steps;
}

function findStepIndexByName(stepId: StepId, steps: SessionStep[]) {
  const foundId = steps.map((s) => s.stepId).findIndex((id) => id === stepId);
  return foundId === -1 ? 0 : foundId;
}

function StepPageContent() {
  const { sessions } = useMigrationSessions();
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('id');
  const currentSession = sessions.find((s) => s.id == sessionId);

  const steps = !!currentSession ? createSteps(currentSession!.workflow) : [];
  const currentStep =
    (searchParams.get('step') as StepId) ?? steps[0]?.stepId ?? undefined;
  const [activeStepIndex, setActiveStepIndex] = useState(
    findStepIndexByName(currentStep, steps)
  );

  const handleStepChange = ({
    detail
  }: {
    detail: { requestedStepIndex: number };
  }) => {
    const nextIndex = detail.requestedStepIndex;
    setActiveStepIndex(nextIndex);

    const currentParams = new URLSearchParams(window.location.search);
    currentParams.set('step', steps[nextIndex].stepId);

    router.replace(`?${currentParams.toString()}`);
  };

  let flashbarItems: FlashbarProps.MessageDefinition[] = [];
  if (currentSession?.workflow === 'freeform') {
    flashbarItems.push({
      type: 'info',
      header: 'Freeform Navigation',
      content: 'In freeform session you can freely navigate between any steps.',
      dismissible: true,
      id: 'freeform-nav',
      onDismiss: () =>
        (flashbarItems = flashbarItems.filter(
          (item) => item.id === 'freeform-nav'
        ))
    });
  }

  if (steps.length === 0) {
    flashbarItems.push({
      type: 'error',
      header: 'Session not found',
      content: `Unable to find session ${sessionId}`,
      id: 'session-not-found',
      action: (
        <Link href="/dashboard">
          <Button>Dashboard</Button>
        </Link>
      )
    });
  }

  return (
    <SpaceBetween size="xxl">
      <Header>Session: {currentSession?.name}</Header>
      <Flashbar items={flashbarItems}></Flashbar>
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
