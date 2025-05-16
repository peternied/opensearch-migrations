'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import TaskTable from './task-table';
import { Box } from '@cloudscape-design/components';
import EstimateCompletionTime from '@/components/time/eta';

export default function Page() {
  return (
    <SpaceBetween size="m">
      <Header variant="h1">Migration tasks dashboard</Header>

      <Container>
        <SpaceBetween size="s">
          <Box>
            Migrate your cluster in small steps, work through all these tasks to
            complete your migration.
          </Box>
          <EstimateCompletionTime
            percentage={18}
            etaSeconds={6 * 4000}
            variant={'overall'}
            label="Estimated remaining work"
          ></EstimateCompletionTime>
          <TaskTable />
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
