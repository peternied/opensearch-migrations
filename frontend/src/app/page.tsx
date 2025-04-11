'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Spinner from '@cloudscape-design/components/spinner';
import Alert from '@cloudscape-design/components/alert';
import Button from '@cloudscape-design/components/button';
import Link from 'next/link';

export default function MigrationAssistantStatusPage() {
  const [isReady, setIsReady] = useState(false);

  return (
    <SpaceBetween size="m">
      <Header variant="h1">
        {isReady ? 'Migration Assistant Ready' : 'Migration Assistant is Deploying'}
      </Header>

      <Container>
        <SpaceBetween size="l">
          {isReady ? (
            <>
              <Box variant="h3">You're all set to begin a migration</Box>
              <Alert statusIconAriaLabel="info" header="Before you begin">
                Review the following tips to ensure you're ready for a smooth migration.
              </Alert>
            </>
          ) : (
            <Box textAlign="center">
              <Spinner size="large" />
              <Box variant="h3" margin={{ top: 's' }}>
                Hang tight — Migration Assistant is currently being deployed.
              </Box>
            </Box>
          )}

          <SpaceBetween size="s">
            <Box variant="h4">1. Get source cluster connection details</Box>
            <Box>
              Identify the URL and authentication credentials for your source OpenSearch cluster.
              These will be required to begin the migration process.
            </Box>

            <Box variant="h4">2. Prepare your target cluster</Box>
            <Box>
              You can configure a fresh target OpenSearch cluster or let Migration Assistant reuse your existing
              managed OpenSearch cluster by providing its ARN.
            </Box>

            <Box variant="h4">3. Plan your migration strategy</Box>
            <Box>
              Decide if you will use a snapshot to backfill data, or set up capture and replay to
              ensure continuity during migration.
            </Box>
          </SpaceBetween>

          <Box>
            {isReady ? (
              <Link href="/step-page?step=0">
                <Button variant="primary">Start a migration</Button>
              </Link>
            ) : (
              <Button variant="normal" onClick={() => setIsReady(true)}>
                Mark as Ready for Testing
              </Button>
            )}
          </Box>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
