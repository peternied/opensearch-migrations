'use client';

import Table from '@cloudscape-design/components/table';
import Button from '@cloudscape-design/components/button';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ButtonDropdown, Header, Icon, StatusIndicator } from '@cloudscape-design/components';
import { SupportPromptGroup } from '@cloudscape-design/chat-components';

interface Task {
  id: string;
  name: string;
  status: 'Pending' | 'Migrated' | 'Complete' | 'Error' | 'Ignored';
  currentStep: number;
}

const initialTasks: Task[] = [
  {
    id: '1',
    name: 'Task - Global metadata',
    status: 'Pending',
    currentStep: 0
  },
  { id: '2', name: 'Task - Index foobar', status: 'Migrated', currentStep: 0 },
  { id: '3', name: 'Task - Indices a,b,c', status: 'Pending', currentStep: 0 },
  { id: '4', name: 'Task - Indices d,e,f', status: 'Ignored', currentStep: 0 },
  {
    id: '6',
    name: 'Switch operations dashboard to point to target cluster',
    status: 'Complete',
    currentStep: 0
  },
  {
    id: '5',
    name: 'Update Elasticserach client',
    status: 'Pending',
    currentStep: 0
  },
  {
    id: '6',
    name: 'Redirect data stream onto target cluster',
    status: 'Pending',
    currentStep: 0
  }
];

function toStatus(
  status: 'Pending' | 'Migrated' | 'Complete' | 'Error' | 'Ignored'
) {
  switch (status) {
    case 'Migrated':
    case 'Complete':
      return 'success';
    case 'Error':
      return 'error';
    case 'Pending':
      return 'pending';
    case 'Ignored':
    default:
      return 'stopped';
  }
}

export default function TaskTable() {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [selectedItems, setSelectedItems] = useState<Task[]>([]);
  const router = useRouter();

  const handleNavigateToWorkflow = (taskId: string) => {
    router.push(`/tasks/workflow?id=${taskId}`);
  };

  const handleMarkAsIgnored = () => {
    setTasks((prevTasks) =>
      prevTasks.map((task) =>
        selectedItems.some((selected) => selected.id === task.id)
          ? { ...task, status: 'Ignored' }
          : task
      )
    );
    setSelectedItems([]);
  };

  return (
    <div style={{ position: 'relative' }}>
      <SpaceBetween size="l" direction="vertical">
        <SpaceBetween direction="horizontal" alignItems="end" size="m">
          <Header variant='h2' actions={
            <SpaceBetween size='m' direction='horizontal' alignItems='end'>
            <Button iconName='gen-ai'>Suggest next task</Button>

            <ButtonDropdown
            // onClick={handleMarkAsIgnored}
            disabled={selectedItems.length === 0} items={[
              {id: 'ignore', itemType: 'action', text: 'Mark as Ignored'}
            ]}>
            Task Actions
          </ButtonDropdown>
          </SpaceBetween>
          }>
            Tasks
          </Header>
          
        </SpaceBetween>
        <Table
          columnDefinitions={[
            { id: 'name', header: 'Task Name', cell: (item) => item.name },
            {
              id: 'status',
              header: 'Status',
              cell: (item) => (
                <StatusIndicator type={toStatus(item.status)}>
                  {item.status}
                </StatusIndicator>
              )
            },
            {
              id: 'workflow',
              header: 'Workflow',
              cell: (item) => (
                <SpaceBetween size="xs" direction="horizontal">
                  <Button onClick={() => handleNavigateToWorkflow(item.id)}>
                    Review
                  </Button>
                </SpaceBetween>
              )
            }
          ]}
          selectionType="multi"
          selectedItems={selectedItems}
          onSelectionChange={({ detail }) =>
            setSelectedItems(detail.selectedItems)
          }
          items={tasks}
          loadingText="Loading tasks"
          empty={<div>No tasks available</div>}
          header="Tasks"
          stickyHeader
        />
      </SpaceBetween>
    </div>
  );
}
