'use client';

import { useState } from 'react';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import ProgressBar from '@cloudscape-design/components/progress-bar';
import Box from '@cloudscape-design/components/box';
import Slider from '@cloudscape-design/components/slider';
import LineChart from '@cloudscape-design/components/line-chart';
import Cards from '@cloudscape-design/components/cards';
import Table from '@cloudscape-design/components/table';
import { StatusIndicator } from '@cloudscape-design/components';

type IndexStatus = 'not-started' | 'in-progress' | 'completed';

type Index = {
  id: string;
  progress: number;
  eta: string;
  status: IndexStatus;
};

const indices: Index[] = [
  { id: 'index-1', progress: 0, eta: '20m', status: 'not-started' },
  { id: 'index-2', progress: 45, eta: '10m', status: 'in-progress' },
  { id: 'index-3', progress: 100, eta: '0m', status: 'completed' }
];

const mockMetrics = [
  {
    name: 'CPU Usage',
    description: 'Percentage of CPU used over time.',
    type: 'Resource',
    size: 'Dynamic',
    data: [
      { x: 0, y: 20 },
      { x: 1, y: 45 },
      { x: 2, y: 70 }
    ]
  },
  {
    name: 'Memory Usage',
    description: 'Percentage of memory used over time.',
    type: 'Resource',
    size: 'Dynamic',
    data: [
      { x: 0, y: 30 },
      { x: 1, y: 55 },
      { x: 2, y: 85 }
    ]
  },
  {
    name: 'JVM Heap',
    description: 'Percentage of JVM heap used over time.',
    type: 'Resource',
    size: 'Dynamic',
    data: [
      { x: 0, y: 50 },
      { x: 1, y: 85 },
      { x: 2, y: 65 }
    ]
  }
];

function calculateMaxEta(workers: Index[]) {
  const times = workers.map((w) => parseInt(w.eta.replace(/[^0-9]/g, '')) || 0);
  const maxTime = Math.max(...times);
  return `${maxTime}m`;
}

export default function Page() {
  const [workerCount, setWorkerCount] = useState(3);
  const overallEta = calculateMaxEta(indices);

  return (
    <SpaceBetween size="l">
      <Container>
        <SpaceBetween size="m">
          <Box>
            During the backfill data from the source will be copied onto the
            target cluster as quickly as possible. Dynamical scaling will be
            used to increase the number of workers, or it can be manually
            controlled at the bottom of the page.
          </Box>
          <StatusIndicator type="in-progress">
            Estimated Time to Completion: {overallEta}
          </StatusIndicator>

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
                      item.status === 'not-started'
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
                  <ProgressBar
                    value={item.progress}
                    label={`ETA: ${item.eta}`}
                  />
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
      </Container>

      <Container>
        <SpaceBetween size="m">
          <Header variant="h2">Cluster Metrics</Header>
          <Cards
            cardDefinition={{
              header: (item) => (
                <SpaceBetween direction={'horizontal'} size={'s'}>
                  <span>{item.name}</span>
                  <StatusIndicator
                    type={
                      item.status === 'red'
                        ? 'error'
                        : item.status === 'warn'
                          ? 'warning'
                          : 'success'
                    }
                  />
                </SpaceBetween>
              ),
              sections: [
                {
                  id: 'description',
                  header: 'Description',
                  content: (item) => item.description
                },
                {
                  id: 'chart',
                  header: 'Metric Trend',
                  content: (item) => (
                    <LineChart
                      series={[
                        { title: item.name, data: item.data, type: 'line' },
                        { title: 'Threshold (80%)', y: 80, type: 'threshold' }
                      ]}
                      xTitle="Time"
                      yTitle="%"
                      hideFilter
                      hideLegend
                      height={100}
                    />
                  )
                }
              ]
            }}
            cardsPerRow={[{ cards: 1 }, { minWidth: 500, cards: 2 }]}
            items={mockMetrics.map((metric) => {
              const maxY = Math.max(...metric.data.map((point) => point.y));
              const currentY = metric.data[metric.data.length - 1].y;
              let status = 'green';
              if (currentY > 80) status = 'red';
              else if (maxY > 80) status = 'warn';
              return {
                ...metric,
                status
              };
            })}
            selectionType="single"
            trackBy="name"
            visibleSections={['description', 'chart']}
          />
        </SpaceBetween>
      </Container>

      <Container>
        <SpaceBetween size="m">
          <Header variant="h2">Worker Tuning</Header>
          <Box>
            <Slider
              value={workerCount}
              onChange={({ detail }) => setWorkerCount(detail.value)}
              min={1}
              max={10}
              step={1}
              tickMarks={true}
            />
            <Box variant="span">Current: {workerCount}</Box>
          </Box>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
