'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Button from '@cloudscape-design/components/button';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Table, { TableProps } from '@cloudscape-design/components/table';
import Link from 'next/link';
import EstimateCompletionTime, { formatTimeDuration } from '@/components/time/eta';
import {
  MigrationSession,
  useMigrationSessions,
  workflowIcon
} from '@/context/migration-session';
import { Box, Icon, Spinner } from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import DemoWrapper from '@/components/demoWrapper';
import { Suspense } from 'react';

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

function nextState(session: MigrationSession, status: StatusType): string {
  if (session.metadata === status) {
    return 'metadata';
  }
  if (session.backfill === status) {
    return 'backfill';
  }
  if (session.replay === status) {
    return 'replay';
  }
  return 'unknown'
}

function isOngoing(session: MigrationSession): boolean {
  return !session.completedAt;
}

function isCompleted(session: MigrationSession): boolean {
  return !!session.completedAt;
}

function statusMessage(session: MigrationSession): React.ReactNode {
  if (overallState(session) === 'in-progress') return <EstimateCompletionTime etaSeconds={session.etaSeconds || Infinity} variant='inline' />;
  if (overallState(session) === 'pending') return `Waiting for input on ${nextState(session, 'pending')}`;
  if (overallState(session) === 'error') return `Error in step ${nextState(session, 'error')}`;
  return '';
}

function actionLabel(session: MigrationSession): JSX.Element {
  const state = overallState(session);
  if (state === 'in-progress') return <Link href={`/session?id=${session.id}`}><Button>Monitor</Button></Link>;
  if (state === 'pending') return <Link href={`/session?id=${session.id}`}><Button>Continue</Button></Link>;
  if (state === 'error') return <Link href={`/session?id=${session.id}`}><Button>Fix</Button></Link>;
  return <span>N/A</span>;
}

export default function MigrationDashboardPage() {
  const { sessions, addDemoSessions, clearSessions } = useMigrationSessions();

  const ongoing = useCollection(sessions.filter(isOngoing), {
    filtering: {
      empty: (
        <Box>
          There are no sessions.{' '}
          <Link href="/create">
            <Button>Create Migration Session</Button>
          </Link>
        </Box>
      ),
      noMatch: <Box>No sessions with filter criteria.</Box>
    },
    sorting: {}
  });

  const completed = useCollection(sessions.filter(isCompleted), {
    filtering: {
      empty: (
        <Box>
          There are no completed sessions.{' '}
        </Box>
      ),
      noMatch: <Box>No sessions with filter criteria.</Box>
    },
    sorting: {}
  });

  const ongoingColumns: TableProps.ColumnDefinition<MigrationSession>[] = [
    {
      id: 'name',
      header: 'Session Name',
      cell: (item) => <><Icon size='small' name={workflowIcon(item.workflow)} alt={item.workflow}/> <Link href={`/session?id=${item.id}`}>{item.name}</Link></>,
      sortingField: 'name',
    },
    {
      id: 'status',
      header: 'Status',
      cell: (item) => <StatusIndicator type={overallState(item)}>{overallState(item)}</StatusIndicator>
    },
    {
      id: 'message',
      header: 'Message',
      cell: (item) => statusMessage(item)
    },
    {
      id: 'action',
      header: 'Action',
      cell: (item) => actionLabel(item)
    }
  ];

  const completedColumns: TableProps.ColumnDefinition<MigrationSession>[] = [
    {
      id: 'name',
      header: 'Session Name',
      cell: (item) => <>
        <Icon size='small' name={workflowIcon(item.workflow)} alt={item.workflow}/>
        <Link href={`/session?id=${item.id}`}>{item.name}</Link>
      </>,
      sortingField: 'name',
    },
    {
      id: 'created',
      header: 'Create Date',
      cell: (item) => (
        <span suppressHydrationWarning>{new Date(item.createdAt).toLocaleDateString()}</span>
      ),
      sortingField: 'createdAt',
    },
    {
      id: 'status',
      header: 'Status',
      cell: () => <StatusIndicator type="success">Completed</StatusIndicator>
    },
    {
      id: 'time',
      header: 'Time',
      cell: (item) =>  item.completedAt && formatTimeDuration(item.completedAt - item.createdAt)
    },
    {
      id: 'size',
      header: 'Migration Size',
      cell: (item) =>
        item.sizeBytes ? `${(item.sizeBytes / (1024 ** 4)).toFixed(1)} TB` : 'N/A'
    }
  ];

  return (
    <Suspense fallback={<Spinner />}>
      <SpaceBetween size="l">
        <Header
          variant="h1"
          actions={
            <Link href="/create">
              <Button variant="primary">Create Migration Session</Button>
            </Link>
          }
        >
          Migration Sessions Dashboard
        </Header>

        <Container header={<Header variant="h2">Ongoing Sessions</Header>}>
          <Table
            {...ongoing.collectionProps}
            items={ongoing.items}
            columnDefinitions={ongoingColumns}
            variant="borderless"
            stickyHeader
          />
        </Container>

        <Container header={<Header variant="h2">Completed Sessions</Header>}>
          <Table
            {...completed.collectionProps}
            items={completed.items}
            columnDefinitions={completedColumns}
            variant="borderless"
            stickyHeader
          />
        </Container>

        <DemoWrapper>
          <SpaceBetween size="m" direction="horizontal">
            <Button onClick={addDemoSessions}>Add Demo Sessions</Button>
            <Button onClick={clearSessions}>Clear Sessions</Button>
          </SpaceBetween>
        </DemoWrapper>
      </SpaceBetween>
    </Suspense>
  );
}
