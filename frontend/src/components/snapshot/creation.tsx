'use client';

import { useState } from 'react';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Table from '@cloudscape-design/components/table';
import Button from '@cloudscape-design/components/button';
import Header from '@cloudscape-design/components/header';
import type { TableProps } from '@cloudscape-design/components/table';
import EstimateCompletionTime from '../time/eta';

type NonCancelableEventHandler<Detail> = (event: { detail: Detail }) => void;
interface IndexEntry {
  name: string;
  documents: number;
  sizeGb: number;
}

const MOCK_INDICES: IndexEntry[] = [
  { name: 'geonames', documents: 150000, sizeGb: 0.3 },
  { name: 'nyc_taxis', documents: 1250000, sizeGb: 22.5 },
  { name: 'percolator', documents: 340000, sizeGb: 0.7 },
  { name: 'logs-191998', documents: 980000, sizeGb: 1.9 },
  { name: 'logs-201998', documents: 670000, sizeGb: 1.3 },
  { name: 'logs-211998', documents: 400000, sizeGb: 0.8 }
];

function calculateEstimatedTime(items: IndexEntry[]) {
  const totalSize = items.reduce((acc, item) => acc + item.sizeGb, 0);
  return Math.ceil(totalSize * 5 * 60);
}

export default function SnapshotCreation() {
  const [selectedItems, setSelectedItems] =
    useState<IndexEntry[]>(MOCK_INDICES);
  const [isSnapshotting, setIsSnapshotting] = useState(false);
  const [snapshotComplete, setSnapshotComplete] = useState(false);
  const [estimatedTime, setEstimatedTime] = useState<number>(
    calculateEstimatedTime(MOCK_INDICES)
  );

  const handleSelectionChange: NonCancelableEventHandler<
    TableProps.SelectionChangeDetail<IndexEntry>
  > = ({ detail }) => {
    const items = detail.selectedItems;
    setSelectedItems(items);
    setEstimatedTime(calculateEstimatedTime(items));
  };

  const handleTakeSnapshot = () => {
    setIsSnapshotting(true);
    setTimeout(() => {
      setIsSnapshotting(false);
      setSnapshotComplete(true);
    }, 5000);
  };

  const columnDefinitions = [
    { id: 'name', header: 'Index name', cell: (item: IndexEntry) => item.name },
    {
      id: 'documents',
      header: 'Documents',
      cell: (item: IndexEntry) => item.documents.toLocaleString()
    },
    {
      id: 'sizeGb',
      header: 'Size',
      cell: (item: IndexEntry) => item.sizeGb.toFixed(2) + ' GB'
    }
  ];

  return (
    <SpaceBetween size="m">
      <Table
        header={
          <Header variant="h3">
            Indexes included in the snapshot
          </Header>
        }
        columnDefinitions={columnDefinitions}
        items={MOCK_INDICES}
        selectedItems={selectedItems}
        // onSelectionChange={handleSelectionChange}
        // selectionType="multi"
        trackBy="name"
        isItemDisabled={() => isSnapshotting || snapshotComplete}
        variant="embedded"
        stickyHeader
      />

      <EstimateCompletionTime
        etaSeconds={estimatedTime}
        variant="overall"
        label="Taking full snapshot"
        status={
          !isSnapshotting && !snapshotComplete
            ? 'pending'
            : isSnapshotting
              ? 'in-progress'
              : 'success'
        }
      ></EstimateCompletionTime>

      {!isSnapshotting && !snapshotComplete && (
        <SpaceBetween size="m">
          <Button
            onClick={handleTakeSnapshot}
            disabled={selectedItems.length === 0}
            variant="primary"
          >
            Take Snapshot
          </Button>
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}
