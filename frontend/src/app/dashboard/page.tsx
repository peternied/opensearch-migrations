'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Table from '@cloudscape-design/components/table';
import Link from 'next/link';
import EstimateCompletionTime from '@/component/time/eta';
import {
  MigrationSession,
  useMigrationSessions
} from '@/context/migration-session';

export type StatusType = 'success' | 'in-progress' | 'pending' | 'error';

function anyOf(status: StatusType, session: MigrationSession): boolean {
  return (
    session.backfill === status ||
    session.backfill === status ||
    session.replay === status
  );
}

function overallState(session: MigrationSession): StatusType {
  if (anyOf('error', session)) {
    return 'error';
  }
  if (anyOf('in-progress', session)) {
    return 'in-progress';
  }
  if (anyOf('pending', session)) {
    return 'pending';
  }
  if (anyOf('success', session)) {
    return 'success';
  }
  return 'error';
}

export default function MigrationDashboardPage() {
  const { sessions } = useMigrationSessions();

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        actions={
          <Link href="/session">
            <Button variant="primary">Create Migration Session</Button>
          </Link>
        }
      >
        Migration Sessions Dashboard
      </Header>

      <Container header={<Header variant="h2">Sessions</Header>}>
        <Table
          items={sessions}
          columnDefinitions={[
            {
              id: 'name',
              header: 'Session Name',
              cell: (item) => (
                <Link href={`/session?id=${item.id}`}>{item.name}</Link>
              )
            },
            {
              id: 'created',
              header: 'Created Date',
              cell: (item) => item.createdAt.toLocaleDateString()
            },
            {
              id: 'overall-state',
              header: 'Overall State',
              cell: (item) => (
                <StatusIndicator type={overallState(item)}>
                  {overallState(item)}
                </StatusIndicator>
              )
            },
            {
              id: 'metadata',
              header: 'Metadata',
              cell: (item) => (
                <StatusIndicator type={item.metadata}>
                  {item.metadata}
                </StatusIndicator>
              )
            },
            {
              id: 'backfill',
              header: 'Backfill',
              cell: (item) => (
                <StatusIndicator type={item.backfill}>
                  {item.backfill}
                </StatusIndicator>
              )
            },
            {
              id: 'replay',
              header: 'Traffic Replay',
              cell: (item) => (
                <StatusIndicator type={item.replay}>
                  {item.replay}
                </StatusIndicator>
              )
            },
            {
              id: 'eta',
              header: 'Estimated Time',
              cell: (item) =>
                item.etaSeconds ? (
                  <EstimateCompletionTime
                    etaSeconds={item.etaSeconds}
                    variant="inline"
                  />
                ) : (
                  'N/A'
                )
            },
            {
              id: 'size',
              header: 'Estimated Size',
              cell: (item) =>
                item.sizeBytes != 0
                  ? (item.sizeBytes / (1024 * 1024 * 1024)).toFixed(2) + ' Gb'
                  : 'N/A'
            }
          ]}
          stickyHeader
          variant="borderless"
        />
      </Container>
    </SpaceBetween>
  );
}
