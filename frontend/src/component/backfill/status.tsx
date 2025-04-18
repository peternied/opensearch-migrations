'use client';

import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import Table from '@cloudscape-design/components/table';
import { StatusIndicator } from '@cloudscape-design/components';
import EstimateCompletionTime, { Status } from '../time/eta';

type Index = {
  id: string;
  progress: number;
  eta: number;
  status: Status;
};

const indices: Index[] = [
  { id: 'index-1', progress: 0, eta: 20 * 60, status: 'pending' },
  { id: 'index-2', progress: 45, eta: 10 * 60, status: 'in-progress' },
  { id: 'index-3', progress: 100, eta: 0, status: 'success' }
];

function calculateMaxEta(workers: Index[]): number {
  const times = workers.map((w) => w.eta || 0);
  return times.reduce((acc, n) => n + acc, 0);
}

function calculateProgressPercent(workers: Index[]): number {
  const workerProgress = workers.map((w) => w.progress || 0);
  const totalProgress = workerProgress.reduce((acc, n) => n + acc, 0);
  return totalProgress / workers.length;
}

export default function Page() {
  const overallEta = calculateMaxEta(indices);
  const overallProgressPercent = calculateProgressPercent(indices);

  return (
    <SpaceBetween size="m">
      <Box>
        During the backfill data from the source will be copied onto the target
        cluster as quickly as possible. Dynamical scaling will be used to
        increase the number of workers, or it can be manually controlled at the
        bottom of the page.
      </Box>
      <EstimateCompletionTime
        status="in-progress"
        etaSeconds={overallEta}
        percentage={overallProgressPercent}
        variant="overall"
        label="All indices backfilled"
      ></EstimateCompletionTime>

      <Table
        columnDefinitions={[
          {
            id: 'id',
            header: 'Index ID',
            cell: (item: Index) => <strong>{item.id}</strong>,
            sortingField: 'id'
          },
          {
            id: 'status',
            header: 'Status',
            cell: (item: Index) => (
              <StatusIndicator
                type={
                  item.status === 'pending'
                    ? 'pending'
                    : item.status === 'in-progress'
                      ? 'in-progress'
                      : 'success'
                }
              >
                {item.status.replace('-', ' ')}
              </StatusIndicator>
            ),
            sortingField: 'status'
          },
          {
            id: 'progress',
            header: 'Progress',
            cell: (item: Index) => (
              <EstimateCompletionTime
                variant="inline"
                etaSeconds={item.eta}
                percentage={item.progress}
                status={item.status}
              ></EstimateCompletionTime>
            )
          }
        ]}
        items={indices}
        trackBy="id"
        header={<Header variant="h2">Index Backfill Status</Header>}
        variant="borderless"
        stickyHeader={true}
      />
    </SpaceBetween>
  );
}
