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
import { StatusIndicator } from '@cloudscape-design/components';

type Worker = {
  id: string;
  progress: number;
  eta: string;
};

const workers: Worker[] = [
  { id: 'worker-1', progress: 75, eta: '5m' },
  { id: 'worker-2', progress: 40, eta: '12m' },
  { id: 'worker-3', progress: 90, eta: '2m' }
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

function calculateMaxEta(workers: Worker[]) {
  const times = workers.map((w) => parseInt(w.eta.replace(/[^0-9]/g, '')));
  const maxTime = Math.max(...times);
  return `${maxTime}m`;
}

export default function Page() {
  const [workerCount, setWorkerCount] = useState(3);
  const overallEta = calculateMaxEta(workers);

  return (
    <SpaceBetween size="l">
      <Container>
        <SpaceBetween size="m">
          <StatusIndicator type="in-progress">
            Estimated Time to Completion: {overallEta}
          </StatusIndicator>
          <SpaceBetween size="s">
            {workers.map((worker) => (
              <Box key={worker.id}>
                <strong>{worker.id}</strong>
                <ProgressBar
                  value={worker.progress}
                  label={`ETA: ${worker.eta}`}
                />
              </Box>
            ))}
          </SpaceBetween>
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
