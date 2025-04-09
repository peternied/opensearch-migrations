'use client';

import { useState } from 'react';
import Button from '@cloudscape-design/components/button';
import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Spinner from '@cloudscape-design/components/spinner';
import Link from '@cloudscape-design/components/link';
import MetadataEvaluation from './evaulation';
import MetadataMigration from './migration';

export default function MetadataWorkflowControl() {
  const [phase, setPhase] = useState<'evaluate' | 'executing' | 'completed'>('evaluate');

  const handleRunMigration = () => {
    setPhase('executing');
    setTimeout(() => setPhase('completed'), 3000);
  };

  return (
    <SpaceBetween size="l">
      {phase === 'evaluate' && (
        <SpaceBetween size="l">
            <MetadataEvaluation />
            <Box textAlign="center">
                <Button variant="primary" onClick={handleRunMigration}>
                Run Migration
                </Button>
            </Box>
        </SpaceBetween>
      )}

      {phase === 'executing' && (
        <Container>
          <Box textAlign="center">
            <SpaceBetween size='l'>
                <Spinner size="large" />
                <Box variant="strong" margin={{ top: 's' }}>
                Migrating indexes and templates...
                </Box>
            </SpaceBetween>
          </Box>
        </Container>
      )}

      {phase === 'completed' && (
        <MetadataMigration />
      )}
    </SpaceBetween>
  );
}
