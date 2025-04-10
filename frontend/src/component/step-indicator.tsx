'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { Link } from '@cloudscape-design/components';

interface StepIndicatorProps {
  currentStep: number;
  steps: string[];
}

export default function StepIndicator({
  currentStep,
  steps
}: StepIndicatorProps) {
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
        return (
          <Link
            key={index}
            onFollow={() => handleStepClick(index)}
            variant={index === currentStep ? 'primary' : 'secondary'}
          >
            {label}
          </Link>
        );
      })}
    </SpaceBetween>
  );
}
