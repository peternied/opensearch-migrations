'use client';

import Table from '@cloudscape-design/components/table';
import Button from '@cloudscape-design/components/button';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface Task {
  id: string;
  name: string;
  status: 'Pending' | 'Migrated' | 'Error' | 'Ignored';
  currentStep: number;
}

const initialTasks: Task[] = [
  { id: '1', name: 'Task - Global metadata', status: 'Pending', currentStep: 0 },
  { id: '2', name: 'Task - Index foobar', status: 'Migrated', currentStep: 0 },
  { id: '3', name: 'Task - Indices a,b,c', status: 'Pending', currentStep: 0 },
  { id: '4', name: 'Task - Indices d,e,f', status: 'Ignored', currentStep: 0 },
];

export default function TaskTable() {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [selectedItems, setSelectedItems] = useState<Task[]>([]);
  const router = useRouter();

  const handleNavigateToWorkflow = (taskId: string) => {
    router.push(`/tasks/workflow?id=${taskId}`);
  };

  const handleMarkAsIgnored = () => {
    setTasks(prevTasks =>
      prevTasks.map(task =>
        selectedItems.some(selected => selected.id === task.id)
          ? { ...task, status: 'Ignored' }
          : task
      )
    );
    setSelectedItems([]);
  };

  return (
    <div style={{ position: 'relative' }}>
      <SpaceBetween size="l" direction="vertical">

        <SpaceBetween direction='horizontal' alignItems='end' size='m'>
            <Button
                onClick={handleMarkAsIgnored}
                disabled={selectedItems.length === 0}
            >
                Mark as Ignored
            </Button>
        </SpaceBetween>
        <Table
          columnDefinitions={[
            { id: 'name', header: 'Task Name', cell: item => item.name },
            { id: 'status', header: 'Status', cell: item => item.status },
            {
              id: 'workflow',
              header: 'Workflow',
              cell: item => (
                <SpaceBetween size="xs" direction="horizontal">
                  <Button onClick={() => handleNavigateToWorkflow(item.id)}>
                    Review
                  </Button>
                </SpaceBetween>
              ),
            },
          ]}
          selectionType="multi"
          selectedItems={selectedItems}
          onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
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
