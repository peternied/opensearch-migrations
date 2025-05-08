'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { useRouter } from 'next/navigation';
import { v4 as uuidv4 } from 'uuid';
import { Spinner } from '@cloudscape-design/components';

import {
  MigrationSession,
  SessionWorkflow,
  useMigrationSessions
} from '@/context/migration-session';
import CreateSessionForm from '@/components/session/create-session-form';

export default function CreateMigrationSessionPage() {
  const router = useRouter();
  const { addSession } = useMigrationSessions();
  const [name, setName] = useState('');
  const [workflow, setWorkflow] = useState<SessionWorkflow>('backfill');
  const [updating, setUpdating] = useState(false);

  const handleAddSession = () => {
    setUpdating(true);
    const newSession: MigrationSession = {
      id: uuidv4(),
      name,
      createdAt: Date.now(),
      metadata: 'pending',
      backfill: 'pending',
      replay: 'pending',
      etaSeconds: null,
      sizeBytes: 0,
      workflow,
      snapshot: 'pending'
    };

    addSession(newSession);
    router.push(`/session?id=${newSession.id}`);
  };

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Create Migration Session</Header>

      <Container>
        <CreateSessionForm
          name={name}
          setName={setName}
          workflow={workflow}
          setWorkflow={setWorkflow}
          onSubmit={handleAddSession}
          loading={updating}
        />
      </Container>
    </SpaceBetween>
  );
}
