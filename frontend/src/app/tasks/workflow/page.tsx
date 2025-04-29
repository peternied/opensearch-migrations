'use client';

import { useParams, useRouter } from 'next/navigation';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Container from '@cloudscape-design/components/container';
import Wizard from '@cloudscape-design/components/wizard';
import Box from '@cloudscape-design/components/box';
import Button from '@cloudscape-design/components/button';
import { ButtonDropdown, KeyValuePairs, KeyValuePairsProps } from '@cloudscape-design/components';

const steps = [
  { id: 'metadata-migration', title: 'Metadata Migration', description: 'Migrate task metadata to new format.' },
  { id: 'percentage-backfill', title: '% Backfill', description: 'Perform a tiny backfill to test data migration.' },
  { id: 'full-backfill', title: 'Full Backfill', description: 'Backfill all data into the new system.' },
  { id: 'percentage-replay', title: '% Replay', description: 'Replay a tiny percentage of production traffic.' },
  { id: 'full-replay', title: 'Full Replay', description: 'Replay all related production traffic.' },
];

interface TaskItem {
  id: string;
  name: string;
  status: string;
}
const associatedItems: TaskItem[] = [
  { id: '1', name: 'Item 1', status: 'Pending' },
  { id: '2', name: 'Item 2', status: 'Migrated' },
  { id: '3', name: 'Item 3', status: 'Error' },
];

export default function TaskWorkflowPage() {
  const { taskId } = useParams();
  const router = useRouter();

  const handleSubmit = () => {
    alert(`Task ${taskId} workflow complete!`);
    router.push('/tasks/manage');
  };

  const handleDoneEarly = () => {
    if (confirm('Are you sure you want to mark this task as done?')) {
      alert(`Task ${taskId} marked as completed early.`);
      router.push('/tasks');
    }
  };

  const handleEditTransformations = () => {
    alert('Edit transformations clicked!');
  };

  function itemToKvp(item: TaskItem): KeyValuePairsProps.Item {
    return {label: item.name, value: item.status };
  }

  const itemKvp = associatedItems.map(itemToKvp);
  itemKvp.push({ label: 'Transformations', value: <Button variant="normal" onClick={handleEditTransformations}>
    Edit Transformations ({3})
  </Button>,})

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Task Workflow for {taskId}</Header>

      <Container>
        <SpaceBetween size="l">
          <Box variant="h2">Task Details</Box>
          <KeyValuePairs items={itemKvp} columns={3} />

          <Box variant="h2">Workflow Progress</Box>
          <Wizard
            i18nStrings={{
              stepNumberLabel: stepNumber => `Step ${stepNumber}`,
              collapsedStepsLabel: (stepNumber, stepsCount) => `Step ${stepNumber} of ${stepsCount}`,
              cancelButton: '',
              previousButton: 'Previous',
              nextButton: 'Next',
              submitButton: 'Finish',
            }}
            secondaryActions={<SpaceBetween size='m' direction='horizontal'><Button>Back to Tasks</Button><Button>Ignore this task</Button></SpaceBetween>}
            steps={steps.map(step => ({
              title: step.title,
              info: step.description,
              content: <div>{step.description}</div>,
            }))}
            onSubmit={handleSubmit}
          />
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
