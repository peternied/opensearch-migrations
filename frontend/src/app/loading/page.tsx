'use client';

import { useEffect, useState } from 'react';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Button from '@cloudscape-design/components/button';
import Link from 'next/link';
import Flashbar, {
  FlashbarProps
} from '@cloudscape-design/components/flashbar';
import ProgressBar from '@cloudscape-design/components/progress-bar';
import DemoWrapper from '@/component/demoWrapper';

const TOTAL_SECONDS = 30 * 60;
const INTERVAL_SECONDS = 1;

export default function MigrationAssistantStatusPage() {
  const [isReady, setIsReady] = useState(false);
  const [progress, setProgress] = useState(0);

  // Simulate deployment progress
  useEffect(() => {
    if (isReady) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const next = prev + 100 / (TOTAL_SECONDS / INTERVAL_SECONDS);
        if (next >= 100) {
          clearInterval(interval);
          setIsReady(true);
          return 100;
        }
        return next;
      });
    }, INTERVAL_SECONDS * 1000);

    return () => clearInterval(interval);
  }, [isReady]);

  const progressFlash: FlashbarProps.MessageDefinition[] = !isReady
    ? [
        {
          type: 'in-progress',
          content: (
            <ProgressBar
              value={Math.min(progress, 100)}
              label="Deploying Migration Assistant"
              description="This can take up to 30 minutes. Migration Assistant will become available once deployment is complete."
              status={progress < 100 ? 'in-progress' : 'success'}
              variant="flash"
            />
          )
        }
      ]
    : [];

  return (
    <SpaceBetween size="m">
      <Flashbar items={progressFlash} />

      <Header variant="h1">
        {isReady
          ? 'Migration Assistant is Ready'
          : 'Preparing Migration Assistant'}
      </Header>

      <SpaceBetween size="l">
        <Box>
          Take a moment to review the following tips. These steps will help
          ensure you&apos;re ready to start migrating once the tool becomes
          available.
        </Box>

        <SpaceBetween size="s">
          <Box variant="h4">1. Get source cluster connection details</Box>
          <Box>
            Identify the URL and authentication credentials for your source
            OpenSearch cluster. These will be required to begin the migration
            process.
          </Box>

          <Box variant="h4">2. Prepare your target cluster</Box>
          <Box>
            You can configure a fresh target OpenSearch cluster or let Migration
            Assistant reuse your existing managed OpenSearch cluster by
            providing its ARN.
          </Box>

          <Box variant="h4">3. Plan your migration strategy</Box>
          <Box>
            Decide if you will use a snapshot to backfill data, or set up
            capture and replay to ensure continuity during migration.
          </Box>
        </SpaceBetween>

        <Box>
          {isReady ? (
            <Link href="/dashboard">
              <Button variant="primary">Go to Dashboard</Button>
            </Link>
          ) : (
            <DemoWrapper keyName="ready-button">
              <Button variant="normal" onClick={() => setIsReady(true)}>
                Mark as Ready for Testing
              </Button>
            </DemoWrapper>
          )}
        </Box>
      </SpaceBetween>
    </SpaceBetween>
  );
}
