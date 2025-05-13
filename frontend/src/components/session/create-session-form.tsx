'use client';

import SpaceBetween from '@cloudscape-design/components/space-between';
import FormField from '@cloudscape-design/components/form-field';
import Input from '@cloudscape-design/components/input';
import Button from '@cloudscape-design/components/button';
import { Spinner } from '@cloudscape-design/components';
import WorkflowPicker from '@/components/session/workflow-picker';
import { SessionWorkflow } from '@/context/migration-session';

interface CreateSessionFormProps {
  name: string;
  setName: (name: string) => void;
  workflow: SessionWorkflow;
  setWorkflow: (workflow: SessionWorkflow) => void;
  onSubmit: () => void;
  loading: boolean;
  showDisabled: boolean;
}

export default function CreateSessionForm({
  name,
  setName,
  workflow,
  setWorkflow,
  onSubmit,
  loading,
  showDisabled
}: CreateSessionFormProps) {
  return (
    <SpaceBetween size="l">
      <FormField label="Migration Session Name">
        <Input
          value={name}
          placeholder="Enter a session name"
          onChange={({ detail }) => setName(detail.value)}
        />
      </FormField>

      <WorkflowPicker showDisabled={showDisabled} value={workflow} onChange={setWorkflow} />

      <SpaceBetween size="m" direction="horizontal">
        <Button
          variant="primary"
          disabled={!name}
          disabledReason="Name is required"
          onClick={onSubmit}
        >
          Create Session
        </Button>
        {loading && <Spinner size="big" />}
      </SpaceBetween>
    </SpaceBetween>
  );
}
