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

type WorkflowOption = {
  value: SessionWorkflow;
  label: string;
  description: string;
};

const WORKFLOW_OPTIONS: WorkflowOption[] = [
  {
    value: 'backfill',
    label: 'Backfill',
    description:
      'Transfer existing historical data to the new system without impacting live traffic.'
  },
  {
    value: 'replay',
    label: 'Traffic Capture/Replay',
    description:
      'Capture live traffic and replay it in the new environment for testing and validation.'
  },
  {
    value: 'full',
    label: 'Combined Capture + Replay',
    description:
      'Perform backfill and then begin traffic capture and replay in a single workflow.'
  },
  {
    value: 'freeform',
    label: 'Freeform Exploration',
    description:
      'Explore the Migration Assistant website without committing to a specific workflow.'
  }
];

export default function CreateMigrationSessionPage() {
  const router = useRouter();
  const { addSession } = useMigrationSessions();
  const [name, setName] = useState('');
  const [updating, setUpdating] = useState(false);
  const [workflow, setWorkflow] = useState('backfill' as SessionWorkflow);

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
      workflow: workflow
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

          <FormField
            label="Workflow Type"
            description="Choose the appropriate workflow."
          >
            <Tiles
              value={workflow}
              onChange={({ detail }) =>
                setWorkflow(detail.value as SessionWorkflow)
              }
              items={WORKFLOW_OPTIONS.map((option) => ({
                value: option.value,
                label: (
                  <SpaceBetween size="xs">
                    <Box display="inline" padding={{ right: 's' }}>
                      <Icon name={workflowIcon(option.value)} size="big" />
                    </Box>
                    <span>{option.label}</span>
                  </SpaceBetween>
                ),
                description: option.description
              }))}
            />
          </FormField>

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
