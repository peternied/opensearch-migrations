'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import Box from '@cloudscape-design/components/box';
import StepIndicator from '@/component/step-indicator';
import { useRouter, useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
const RequestPlaybackTimeline = dynamic(() => import('@/component/playback'), { ssr: false });

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

          {stepIndex == 2 && (
              <RequestPlaybackTimeline
                data={[
                  { timestamp: Date.parse("2025-04-02"), requestCount: 30 },
                  { timestamp: Date.parse("2025-04-03"), requestCount: 400 },
                  { timestamp: Date.parse("2025-04-04"), requestCount: 8000 },
                  { timestamp: Date.parse("2025-04-05"), requestCount: 43000 },
                  { timestamp: Date.parse("2025-04-06"), requestCount: 4100 },
                  { timestamp: Date.parse("2025-04-07"), requestCount: 200 },
                ]}
                playbackMarkers={[{label: 'a', timestamp: Date.parse("2025-04-04")}]}
                firstRequestTimestamp={Date.parse("2025-04-02")}
              />
            )}


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
