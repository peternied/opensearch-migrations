'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Box from '@cloudscape-design/components/box';
import StepIndicator from '@/component/step-indicator';
import { useRouter, useSearchParams } from 'next/navigation';

const stepLabels = ['Select Source', 'Select Target', 'Metadata', 'Backfill', 'Replay', 'Completion'];

const stepComponents = [
  <Box variant="p" key="source">Select Source Content</Box>,
  <Box variant="p" key="target">Select Target Content</Box>,
  <Box variant="p" key="metadata">Metadata Content</Box>,
  <Box variant="p" key="backfill">Backfill Content</Box>,
  <Box variant="p" key="replay">Replayer Content</Box>,
  <Box variant="p" key="review">Review Content</Box>,
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
      <Header variant="h1">Example Multi-Step Flow</Header>

      <StepIndicator
        currentStep={stepIndex}
        steps={stepLabels}
      />

      <Container>
        <SpaceBetween size="l">
          <Box variant="p">
            This is content for: <strong>{stepLabels[stepIndex]}</strong>
          </Box>

          <Box textAlign="right">
            <SpaceBetween direction="horizontal" size="s">
              <Button onClick={handleBack} disabled={stepIndex === 0}>Back</Button>
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
