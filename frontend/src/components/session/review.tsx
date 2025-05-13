'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Select from '@cloudscape-design/components/select';
import Button from '@cloudscape-design/components/button';
import {
  Box,
  KeyValuePairs,
  LineChart,
  Link,
  StatusIndicator,
  StatusIndicatorProps
} from '@cloudscape-design/components';
import { MigrationSession } from '@/context/migration-session';
import CreateSessionForm from './create-session-form';
import DemoWrapper from '../demoWrapper';

// Format utilities
function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}

function formatBytes(bytes: number): string {
  const mb = bytes / (1024 * 1024 * 1024);
  return `${mb.toFixed(2)} GB`;
}

function generateSeries(durationSeconds: number, average: number, label: string, startTime: number) {
  const interval = 300;
  const points = Math.floor(durationSeconds / interval);
  const data = Array.from({ length: points }, (_, i) => ({
    x: new Date(startTime + i * interval * 1000).getTime(),
    y: average + (Math.random() - 0.5) * average * 0.3
  }));
  return [{ title: label, type: 'line', data }];
}

// Dummy data (same as before)...
// Dummy sessions
const newSession: MigrationSession | null = null;

const emptySession: MigrationSession = {
  id: 'session-empty',
  name: 'Metadata Only',
  createdAt: Date.now(),
  etaSeconds: 0,
  sizeBytes: 0,
  metadata: 'pending',
  backfill: 'pending',
  replay: 'pending',
  workflow: 'backfill',
  snapshot: 'pending'
};

const snapshotSession: MigrationSession = {
  id: 'session-snapshot',
  name: 'Metadata Only',
  createdAt: Date.now(),
  etaSeconds: 0,
  sizeBytes: 0,
  metadata: 'pending',
  backfill: 'pending',
  replay: 'pending',
  workflow: 'backfill',
  snapshot: 'in-progress'
};

const metadataSession: MigrationSession = {
  id: 'session-meta',
  name: 'Metadata Only',
  createdAt: Date.now(),
  etaSeconds: 0,
  sizeBytes: 0,
  metadata: 'pending',
  metadataDetails: {
    status: 'in-progress',
    indices: 10,
    templates: 4,
    aliases: 2
  },
  backfill: 'pending',
  replay: 'pending',
  workflow: 'backfill',
  snapshot: 'success'
};

const inProgressSession: MigrationSession = {
  id: 'session-progress',
  name: 'Backfill In Progress',
  createdAt: Date.now() - 3600000,
  etaSeconds: 3600,
  sizeBytes: 8589934592,
  metadata: 'success',
  metadataDetails: {
    status: 'completed',
    indices: 42,
    templates: 10,
    aliases: 15
  },
  backfill: 'in-progress',
  backfillDetails: {
    status: 'in-progress',
    durationSeconds: 1800,
    throughputMbPerSec: 40,
    sizeBytes: 4294967296,
    docs: '12,000,000'
  },
  replay: 'pending',
  workflow: 'full',
  snapshot: 'pending'
};

const completeSession: MigrationSession = {
  id: 'session-complete',
  name: 'Completed Migration',
  createdAt: Date.now() - 86400000,
  etaSeconds: 0,
  sizeBytes: 12884901888,
  metadata: 'success',
  metadataDetails: {
    status: 'completed',
    indices: 42,
    templates: 10,
    aliases: 15
  },
  backfill: 'success',
  backfillDetails: {
    status: 'completed',
    durationSeconds: 7200,
    throughputMbPerSec: 75.5,
    sizeBytes: 10884901888,
    docs: '23,420,233'
  },
  replay: 'success',
  replayDetails: {
    status: 'completed',
    toSingularitySeconds: 3600,
    toCutoverSeconds: 1800,
    sizeBytes: 2884901888,
    requests: '342,232,322'
  },
  workflow: 'full',
  snapshot: 'success'
};

const getNextStageAction = (session: MigrationSession | null) => {
  if (!session) return null;

  const actions = [];

  if (!session.snapshot) {
    actions.push({
      label: session.snapshot === 'in-progress' ? 'Retry Snapshot' : 'Start Snapshot',
      onClick: () => alert('Snapshot action triggered')
    });
  } else if (!session.metadata) {
    actions.push({
      label: session.metadata === 'in-progress' ? 'Retry Metadata' : 'Start Metadata',
      onClick: () => alert('Metadata action triggered')
    });
  } else if (!session.backfill) {
    actions.push({
      label: session.backfill === 'in-progress' ? 'Retry Backfill' : 'Start Backfill',
      onClick: () => alert('Backfill action triggered')
    });
  }

  return actions;
};

export default function MigrationSessionReviewPage() {
  const [selectedSession, setSelectedSession] = useState('none');
  const [name, setName] = useState('');

  const sessionOptions = [
    { label: 'None', value: 'none' },
    { label: 'New empty session', value: 'empty'},
    { label: 'Snapshot', value: 'snapshot'},
    { label: 'Metadata', value: 'metadata' },
    { label: 'Backfill In Progress', value: 'in-progress' },
    { label: 'Completed', value: 'completed' }
  ];

  let session: MigrationSession | null = null;
  switch (selectedSession) {
    case 'empty':
      session = emptySession;
      break;
    case 'snapshot':
      session = snapshotSession;
      break;
    case 'metadata':
      session = metadataSession;
      break;
    case 'in-progress':
      session = inProgressSession;
      break;
    case 'completed':
      session = completeSession;
      break;
    default:
      session = null;
  }

  const getOverallStatus = (): { type: StatusIndicatorProps.Type; label: string } => {
    if (!session) return { type: 'pending', label: 'No Session Selected' };
    if (session.backfill === 'pending' || session.metadata === 'pending' || session.snapshot === 'pending') {
      return { type: 'pending', label: 'Waiting on user input' };
    }
    if (session.backfill === 'in-progress' || session.metadata === 'in-progress' || session.snapshot === 'in-progress') {
      return { type: 'in-progress', label: 'Migration In Progress' };
    }
    return { type: 'success', label: 'Migration Completed' };
  };

  const backfillData = session?.backfillDetails
    ? generateSeries(
        session.backfillDetails.durationSeconds,
        session.backfillDetails.throughputMbPerSec,
        'Throughput',
        session.createdAt
      )
    : [];

  const nextActions = getNextStageAction(session);

  return (
    <SpaceBetween size="xl">
      {/* <DemoWrapper>s */}
      <Select
        selectedOption={sessionOptions.find((o) => o.value === selectedSession)}
        onChange={({ detail }) => setSelectedSession(detail.selectedOption.value)}
        options={sessionOptions}
        selectedAriaLabel="Session"
        placeholder="Select a session"
      />
      {/* </DemoWrapper> */}

      {!session && (
        <>
        <Container header={<Header variant='h2'>Create a migration session</Header>}>
        <SpaceBetween size='m' direction='vertical'>
          <Box>
            To start a migration name the session.
          </Box>
            <CreateSessionForm
              name={name}
              setName={setName}
              workflow={'backfill'}
              setWorkflow={() => {}}
              onSubmit={() => {}}
              loading={false}
              showDisabled={false}
            />
            </SpaceBetween>
        </Container>
        </>
      )}

      {session && (
        <SpaceBetween size="l">
          <Container
            header={
              <Header variant="h2" actions={nextActions?.length ? <Button onClick={nextActions[0].onClick}>{nextActions[0].label}</Button> : undefined}>
                Session Overview
              </Header>
            }
          >
            <KeyValuePairs
              columns={2}
              items={[
                { label: 'Session', value: session.name },
                { label: 'Created At', value: new Date(session.createdAt).toLocaleString() },
                // { label: 'Total Size', value: formatBytes(session.sizeBytes) },
                {
                  label: 'Migration Status',
                  value: (
                    <StatusIndicator type={getOverallStatus().type}>
                      {getOverallStatus().label}
                    </StatusIndicator>
                  )
                }
              ]}
            />
          </Container>

          {/* Snapshot */}
          <Container
            header={
              <Header variant="h2" actions={<Button>{session?.snapshot === 'pending' ? "Create" : "Recreate"} Snapshot</Button>}>
                Snapshot
              </Header>
            }
          >
            <KeyValuePairs
              columns={2}
              items={[
                {
                  label: 'Status',
                  value: (
                    <StatusIndicator type={session.snapshot || 'pending'}>Created</StatusIndicator>
                  )
                },
                {
                  label: 'Completed',
                  value: '17 minutes ago' 
                }
                // {
                //   label: 'Snapshot Logs',
                //   value: (
                //     <Link href="#">View snapshot logs</Link>
                //   )
                // }
              ]}
            />
          </Container>

          {/* Metadata */}
          {session.metadataDetails && (
            <Container header={<Header variant="h2" actions={<Button>{session?.metadata === 'pending' ? "Migrate" : "Recreate"} Metadata</Button>}>Metadata</Header>}>
              <KeyValuePairs
                columns={2}
                items={[
                  { label: 'Status', value: <StatusIndicator type={session.metadata}>Not started</StatusIndicator> },
                  {
                    label: 'Completed',
                    value: '6 minutes ago' 
                  },
                  { label: 'Indices', value: session.metadataDetails.indices },
                  { label: 'Templates', value: session.metadataDetails.templates },
                  { label: 'Aliases', value: session.metadataDetails.aliases },
                  // {
                  //   label: 'Raw Logs',
                  //   value: <Link href="#">Metadata migration logs</Link>
                  // }
                  
                ]}
              />
            </Container>
          )}

          {/* Backfill */}
          {session.backfillDetails && (
            <Container header={<Header variant="h2" actions={<Button>Re-run Backfill</Button>}>Backfill</Header>}>
              <SpaceBetween size="xxl">
                <KeyValuePairs
                  columns={2}
                  items={[
                    { label: 'Status', value: <StatusIndicator type={session.backfill}>In Progress</StatusIndicator> },
                    { label: 'Completed', value: '-' },
                    { label: 'Transferred', value: formatBytes(session.backfillDetails.sizeBytes) },
                    { label: 'Documents', value: session.backfillDetails.docs },
                    {
                      label: 'Duration',
                      value: formatDuration(session.backfillDetails.durationSeconds)
                    },
                    {
                      label: 'Throughput (MB/sec)',
                      value: session.backfillDetails.throughputMbPerSec.toFixed(2)
                    },
                    // {
                    //   label: 'Raw Logs',
                    //   value: <Link href="#">96 worker logs</Link>
                    // }
                  ]}
                />
                <LineChart
                  series={backfillData}
                  xTitle="Time"
                  yTitle="MB/sec"
                  height={250}
                  ariaLabel="Backfill Throughput"
                  hideLegend
                  hideFilter
                  xTickFormatter={(e) =>
                    new Date(e).toLocaleTimeString('en-US', { hour12: true })
                  }
                />
              </SpaceBetween>
            </Container>
          )}
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}
