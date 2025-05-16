'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Table from '@cloudscape-design/components/table';
import Button from '@cloudscape-design/components/button';
import { useState } from 'react';
import {
  Box,
  FormField,
  Icon,
  Input,
  StatusIndicator,
  TextFilter
} from '@cloudscape-design/components';
import SupportPromptGroup from "@cloudscape-design/chat-components/support-prompt-group";

interface Index {
  name: string;
  status: 'available' | 'assigned' | 'ignored';
}

const mockIndices: Index[] = [
  { name: 'Global Metadata', status: 'available' },
  { name: 'index-a', status: 'available' },
  { name: 'index-b', status: 'available' },
  { name: 'index-c', status: 'available' },
  { name: 'index-d', status: 'available' },
  { name: 'index-e', status: 'available' },
  { name: 'index-f', status: 'available' },
  { name: 'index-foobar', status: 'available' }
];

function toStatus(status: 'available' | 'assigned' | 'ignored') {
  switch (status) {
    case 'ignored':
      return 'stopped';
    case 'assigned':
      return 'success';
    case 'available':
    default:
      return 'pending';
  }
}

export default function SourceCaptureAndTaskCreationPage() {
  const [selectedItems, setSelectedItems] = useState<Index[]>([]);
  const [indices, setIndices] = useState(mockIndices);

  const handleIgnore = (item: Index) => {
    setIndices((prev) =>
      prev.map((i) => (i.name === item.name ? { ...i, status: 'ignored' } : i))
    );
    setSelectedItems((prev) => prev.filter((i) => i.name !== item.name));
  };

  const handleCreateTask = () => {
    console.log('Creating task with indices:', selectedItems);
    selectedItems.forEach((i) => (i.status = 'assigned'));
    // Here you would call your backend or update your app state
    setSelectedItems([]);
  };

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Create migration tasks</Header>

      <Container>
        <SpaceBetween size="s">
          <Header variant="h3">Tasks from cluster</Header>
          <Box>
            Reading data from the source cluster, select items to migrate and
            group logical items together or add them one by one.
          </Box>
          <Table
            filter={<TextFilter filteringText={''}></TextFilter>}
            columnDefinitions={[
              { header: 'Index Name', cell: (item) => item.name },
              {
                header: 'Status',
                cell: (item) => (
                  <StatusIndicator type={toStatus(item.status)}>
                    {item.status}
                  </StatusIndicator>
                )
              },
              {
                header: 'Actions',
                cell: (item) =>
                  item.status !== 'ignored' && (
                    <Button
                      variant="normal"
                      onClick={() => handleIgnore(item)}
                    >
                      Ignore
                    </Button>
                  )
              }
            ]}
            items={indices.filter((i) => i.status !== 'ignored')}
            selectionType="multi"
            selectedItems={selectedItems}
            onSelectionChange={({ detail }) =>
              setSelectedItems(detail.selectedItems)
            }
          />

          <SpaceBetween direction="vertical" size="m">
            <FormField label="Task name">
              <Input value={''} onChange={() => ''} />
            </FormField>

            <Button
              variant="primary"
              onClick={handleCreateTask}
              disabled={selectedItems.length === 0}
            >
              Create Task Association
            </Button>
          </SpaceBetween>
          <Header variant='h3'><Icon name='gen-ai'></Icon> Suggest grouping</Header>
          <SupportPromptGroup items={[
            {id: '1', text: 'Index Types'},
            {id: '2', text: 'Data Size'},
            {id: '3', text: 'Recent Usage'},
          ]} onItemClick={undefined} ariaLabel={''} alignment='horizontal'></SupportPromptGroup>
        </SpaceBetween>
      </Container>
      <Container>
        <SpaceBetween size="s">
          <Header variant="h3">Create custom task</Header>
          <Box>
            Define a custom task that needs to be done to complete the
            migration.
          </Box>
          <FormField label="Task name">
            <Input value={''} placeholder={'Client sdk migration'} />
          </FormField>
          <FormField label="Task Description">
            <Input
              value={''}
              placeholder="Migrate from Elasticsearch 7.10 java client onto OpenSearch 2.19 version"
              onChange={() => ''}
            />
          </FormField>

          <Button
            variant="primary"
            onClick={handleCreateTask}
            disabled={selectedItems.length === 0}
          >
            Create Task
          </Button>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
