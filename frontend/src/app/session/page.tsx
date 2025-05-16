'use client';

import { Suspense, useState } from 'react';
import SourceSelector from '@/components/connection/connection-source-selector';
import Connection from '@/components/connection/remote-connection';
import BackfillStatusDashboard from '@/components/backfill/status';
import RequestTimeline from '@/components/capture/request-timeline';
import {
  Box,
  Button,
  Container,
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
  MigrationSession,
  SessionWorkflow,
  useMigrationSessions
} from '@/context/migration-session';
import CaptureProxiesOverview from '@/components/capture/captured-overview';
import MetadataEvaluationAndMigration from '@/components/metadata/evaulation';
import MigrationPath from '@/components/connection/migration-path';

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

function findStepIndexByName(stepId: StepId, steps: SessionStep[]) {
  const foundId = steps.map((s) => s.stepId).findIndex((id) => id === stepId);
  return foundId === -1 ? 0 : foundId;
}

function StepPageContent() {
  const { sessions } = useMigrationSessions();
  const router = useRouter();
  const searchParams = useSearchParams();
  // const sessionId = searchParams.get('id');
  // const currentSession = sessions.find((s) => s.id == sessionId);
  const currentSession: MigrationSession =   {
    id: 'beta',
    name: 'Contoso Corp - Sales',
    createdAt: new Date('2024-04-18').getTime(),
    snapshot: 'success',
    metadata: 'success',
    backfill: 'pending',
    replay: 'pending',
    etaSeconds: null,
    sizeBytes: 0,
    workflow: 'backfill'
  };
  const sessionId = "1"

  const stepDefinitions: SessionStep[] = [
    {
      title: 'Source Information',
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
      title: 'Target Information',
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
      content: <MetadataEvaluationAndMigration session={currentSession} />,
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
    return steps;
  }

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
    <SpaceBetween size='xxl'>
      <Header>Migration Session: {currentSession?.name}</Header>
      <Container>
      <Flashbar items={flashbarItems}></Flashbar>
      <SpaceBetween size='l'>
      <MigrationPath></MigrationPath>
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
    </Container>
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
