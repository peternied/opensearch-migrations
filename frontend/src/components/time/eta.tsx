'use client';

import Box from '@cloudscape-design/components/box';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import ProgressBar from '@cloudscape-design/components/progress-bar';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';

export type Variant = 'overall' | 'inline';
export type Status = 'in-progress' | 'pending' | 'success' | 'error';

interface EstimateCompletionTimeProps {
  variant: Variant;
  etaSeconds: number;
  percentage?: number;
  status?: Status;
  label?: string;
  errorMessage?: string;
}

export function formatTimeDuration(seconds: number): string {
  if (isNaN(seconds)) return 'unknown';
  if (seconds <= 0) return 'less than a second';

  const units = [
    { label: 'day', value: Math.floor(seconds / 86400) },
    { label: 'hr', value: Math.floor((seconds % 86400) / 3600) },
    { label: 'min', value: Math.floor((seconds % 3600) / 60) },
    { label: 'sec', value: seconds % 60 }
  ];

  const significant = units.filter((u) => u.value > 0).slice(0, 2);

  return significant
    .map((u) => `${u.value} ${u.label}${u.value > 1 ? 's' : ''}`)
    .join(' ');
}

function formatPercent(value: number): string {
  return value.toFixed(2);
}

export default function EstimateCompletionTime({
  variant,
  etaSeconds,
  percentage,
  status = 'in-progress',
  label = 'Estimated Completion Time',
  errorMessage: error
}: EstimateCompletionTimeProps) {
  const formattedETA = formatTimeDuration(etaSeconds);
  const progressLabel =
    status === 'success' ? 'Complete' : percentage !== undefined ? `${formatPercent(percentage)}%` : 'In Progress';

  if (variant === 'overall') {
    return (
      <Box>
      <Header variant="h2">{label}</Header>
        <SpaceBetween size="m">
          <ProgressBar
            value={percentage}
            // label={`Progress: ${progressLabel}`}
            label={`Estimated time remaining: ${formattedETA}`}
            status={
              status === 'success'
                ? 'success'
                : status === 'error'
                  ? 'error'
                  : 'in-progress'
            }
          />
          <StatusIndicator type={status}>
            {error !== undefined
              ? error
              : status === 'in-progress'
                ? 'In Progress'
                : status === 'success'
                  ? 'Completed'
                  : status}
          </StatusIndicator>
        </SpaceBetween>
      </Box>
    );
  }

  // Variant === 'inline'
  return (
    <Box>
      <StatusIndicator type={status}>
        {percentage !== undefined
          ? percentage >= 100 
            ? `${formatPercent(percentage)}%`
            : `${formatPercent(percentage)}% • ETA: ${formattedETA}`
          : `ETA: ${formattedETA}`}
      </StatusIndicator>
    </Box>
  );
}
