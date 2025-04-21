'use client';

import { useState } from 'react';
import Button from '@cloudscape-design/components/button';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Spinner from '@cloudscape-design/components/spinner';
import MetadataEvaluation from './evaulation';
import MetadataMigration from './migration';
import DemoWrapper from '../demoWrapper';

export default function MetadataWorkflowControl() {
  const [phase, setPhase] = useState<'evaluate' | 'executing' | 'completed'>(
    'evaluate'
  );

  const handleRunMigration = () => {
    setPhase('executing');
    setTimeout(() => setPhase('completed'), 3000);
  };

  return (
    <SpaceBetween size="l">
      <Box>
        Cluster metadata includes indices, index templates, and aliases. This
        process provides feedback in near real-time to allow for modifications
        to the includes items.
      </Box>
      {phase === 'evaluate' && (
        <SpaceBetween size="l">
          <MetadataEvaluation />
          <DemoWrapper keyName='run-mtd-migration'>
            <Box>
              <Button variant="primary" onClick={handleRunMigration}>
                Run Migration
              </Button>
            </Box>
          </DemoWrapper>
        </SpaceBetween>
      )}

      {phase === 'executing' && (
        <Box textAlign="center">
          <SpaceBetween size="l">
            <Spinner size="large" />
            <Box variant="strong" margin={{ top: 's' }}>
              Migrating indexes and templates...
            </Box>
          </SpaceBetween>
        </Box>
      )}

      {phase === 'completed' && <MetadataMigration />}
    </SpaceBetween>
  );
}
