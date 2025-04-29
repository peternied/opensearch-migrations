'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Table from '@cloudscape-design/components/table';
import Button from '@cloudscape-design/components/button';
import { useState } from 'react';

interface Index {
    name: string;
    status: string;
} 

const mockIndices: Index[] = [
  { name: 'index-1', status: 'available' },
  { name: 'index-2', status: 'available' },
  { name: 'index-3', status: 'available' },
];

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
    // Here you would call your backend or update your app state
    setSelectedItems([]);
  };

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Source Capture and Task Creation</Header>

      <Container>
        <SpaceBetween size="s">
          <Table
            columnDefinitions={[
              { header: 'Index Name', cell: (item) => item.name },
              { header: 'Status', cell: (item) => item.status },
              {
                header: 'Actions',
                cell: (item) =>
                  item.status !== 'ignored' && (
                    <Button
                      variant="inline-link"
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
            onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
          />

          <Button
            variant="primary"
            onClick={handleCreateTask}
            disabled={selectedItems.length === 0}
          >
            Create Task Association
          </Button>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
