'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { useMigrationSessions } from '@/context/migration-session';
import { StatusIndicator } from '@cloudscape-design/components';

const statusMap: Record<string, 'success' | 'in-progress' | 'pending'> = {
  completed: 'success',
  running: 'in-progress',
  pending: 'pending'
};

export default function Page() {
  const { sessions } = useMigrationSessions();

  return (
    <Container header={<Header variant="h2">Migration Sessions</Header>}>
      <SpaceBetween size="s">
        {sessions.map((session) => (
          <div key={session.id}>
            <strong>{session.name}</strong> —{' '}
            <StatusIndicator type={statusMap[session.status]}>
              {session.status}
            </StatusIndicator>
            <div style={{ fontSize: '0.85em', color: '#666' }}>
              Created at: {new Date(session.createdAt).toLocaleString()}
            </div>
          </div>
        ))}
      </SpaceBetween>
    </Container>
  );
}
