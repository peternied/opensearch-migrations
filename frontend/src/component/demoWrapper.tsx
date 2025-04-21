'use client';

import Box from '@cloudscape-design/components/box';
import SpaceBetween from '@cloudscape-design/components/space-between';
import type { ReactNode } from 'react';

interface DemoWrapperProps {
  children: ReactNode;
  label?: string;
  keyName: string;
}

export default function DemoWrapper({
  children,
  label = 'Demo Only',
  keyName
}: DemoWrapperProps) {
  const styles = {
    orange: {
      backgroundColor: '#fff4e5',
      borderColor: '#ec7211'
    }
  };

  const current = styles['orange'];

  return (
    <div
      style={{
        backgroundColor: current.backgroundColor,
        border: `2px dashed ${current.borderColor}`,
        borderRadius: '8px',
        padding: '2px'
      }}
    >
      <SpaceBetween size="xs" key={keyName}>
        <Box fontSize="body-s" color="text-status-warning">
          ⚠️ {label}
        </Box>
        {children}
      </SpaceBetween>
    </div>
  );
}
