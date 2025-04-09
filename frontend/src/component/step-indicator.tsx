'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box, { BoxProps } from '@cloudscape-design/components/box';
import { Button, Link } from '@cloudscape-design/components';

interface StepIndicatorProps {
  currentStep: number;
  steps: string[];
}

export default function StepIndicator({ currentStep, steps }: StepIndicatorProps) {

  const router = useRouter();
  const searchParams = useSearchParams();

  const handleStepClick = (stepIndex: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('step', stepIndex.toString());
    router.push(`?${params.toString()}`);
  };

  return (
    <SpaceBetween direction="horizontal" size="s">
      {steps.map((label, index) => {
        let color: BoxProps.Color = 'inherit';
        if (index < currentStep) color = 'text-status-inactive';
        else if (index === currentStep) color = 'text-status-info';

        return (
          <Box
            key={index}
            color={color}
            fontWeight={index === currentStep ? 'bold' : 'normal'}
          >
             <Link onFollow={() => handleStepClick(index)} variant="secondary">
              {label}
            </Link>
          </Box>
        );
      })}
    </SpaceBetween>
  );
}
