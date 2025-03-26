'use client';

import SpaceBetween from '@cloudscape-design/components/space-between';
import Box, { BoxProps } from '@cloudscape-design/components/box';

interface StepIndicatorProps {
  currentStep: number;
  steps: string[];
}

export default function StepIndicator({ currentStep, steps }: StepIndicatorProps) {
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
            {label}
            {index < steps.length - 1 && <span style={{ margin: '0 8px' }}>|</span>}
          </Box>
        );
      })}
    </SpaceBetween>
  );
}
