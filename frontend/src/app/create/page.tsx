'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import Box from '@cloudscape-design/components/box';
import Icon from '@cloudscape-design/components/icon';
import Button from '@cloudscape-design/components/button';
import Tiles from '@cloudscape-design/components/tiles';
import DemoWrapper from '@/components/demoWrapper';
import {
  MigrationSession,
  SessionWorkflow,
  useMigrationSessions,
  workflowIcon
} from '@/context/migration-session';
import { v4 as uuidv4 } from 'uuid';
import { useRouter } from 'next/navigation';
import { Spinner } from '@cloudscape-design/components';
import WorkflowPicker from '@/components/session/workflow-picker';

export default function CreateMigrationSessionPage() {
  const router = useRouter();
  const { addSession } = useMigrationSessions();
  const [name, setName] = useState('');
  const [updating, setUpdating] = useState(false);
  const [workflow, setWorkflow] = useState<SessionWorkflow>('backfill');

  const handleAddSession = () => {
    setUpdating(true);
    const newSession: MigrationSession = {
      id: uuidv4(),
      name: name,
      createdAt: Date.now(),
      metadata: 'pending',
      backfill: 'pending',
      replay: 'pending',
      etaSeconds: null,
      sizeBytes: 0,
      workflow: 'backfill',
      snapshot: 'pending'
    };

    addSession(newSession);
    router.push(`/session?id=${newSession.id}`);
  };

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Create Migration Session</Header>

      <Container>
        <SpaceBetween size="l">
          <FormField label="Migration Session Name">
            <Input
              value={name}
              placeholder="Enter a session name"
              onChange={({ detail }) => setName(detail.value)}
            />
          </FormField>

          <WorkflowPicker value={workflow} onChange={setWorkflow} />

          <SpaceBetween size="m" direction="horizontal">
            <Button
              variant="primary"
              disabled={!name}
              disabledReason="Name is required"
              onClick={handleAddSession}
            >
              Create Session
            </Button>
            {updating && <Spinner size="big"></Spinner>}
          </SpaceBetween>
          <DemoWrapper>Icons are place holders</DemoWrapper>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
