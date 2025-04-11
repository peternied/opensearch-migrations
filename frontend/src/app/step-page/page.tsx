'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Box from '@cloudscape-design/components/box';
import StepIndicator from '@/component/step-indicator';
import { useRouter, useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import SourceSelector from '@/component/source-selector';
import TargetConnection from '@/component/connection/target';
import MetadataWorkflowControl from '@/component/metadata/selection';
import BackfillStatusDashboard from '@/component/backfill/status';
import SnapshotCreation from '@/component/snapshot/creation';
const RequestPlaybackTimeline = dynamic(() => import('@/component/playback'), {
  ssr: false
});

const stepLabels = [
  'Select Source',
  'Traffic Capture',
  'Select Target',
  'Create Snapshot',
  'Metadata',
  'Backfill',
  'Traffic Replay',
  'Completion'
];

const stepComponents = [
  <Box key="source">
    <Header>Select Source</Header>
    <SourceSelector />
  </Box>,
  <Box key="capture">
    <Header>Traffic Capture</Header>
    <RequestPlaybackTimeline />
  </Box>,
  <Box key="target">
    <Header>Select Target</Header>
    <TargetConnection />
  </Box>,
  <Box key="snapshot">
    <Header>Create Snapshot</Header>
    <SnapshotCreation />
  </Box>,
  <Box key="metadata">
    <Header>Metadata</Header>
    <MetadataWorkflowControl />
  </Box>,
  <Box key="backfill">
    <Header>Backfill</Header>
    <BackfillStatusDashboard />
  </Box>,
  <Box key="replay">
    <Header>Replayer</Header>
  </Box>,
  <Box key="review">
    <Header>Review</Header>
  </Box>
];

export default function StepPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const stepIndex = parseInt(searchParams.get('step') || '0');
  const totalSteps = stepLabels.length;

  const handleContinue = () => {
    if (stepIndex < totalSteps - 1) {
      router.push(`/step-page?step=${stepIndex + 1}`);
    }
  };

  const handleBack = () => {
    if (stepIndex > 0) {
      router.push(`/step-page?step=${stepIndex - 1}`);
    }
  };

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Migration Workflow</Header>

      <StepIndicator currentStep={stepIndex} steps={stepLabels} />

      <Container>
        <SpaceBetween size="l">
          {stepComponents[stepIndex]}
          <Box textAlign="right">
            <SpaceBetween direction="horizontal" size="s">
              <Button onClick={handleBack} disabled={stepIndex === 0}>
                Back
              </Button>
              <Button
                variant="primary"
                onClick={handleContinue}
                disabled={stepIndex >= totalSteps - 1}
              >
                {stepIndex >= totalSteps - 1 ? 'Completed' : 'Continue'}
              </Button>
            </SpaceBetween>
          </Box>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
