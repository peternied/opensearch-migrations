'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import TaskTable from './task-table';

export default function Page() {
  return (
    <SpaceBetween size="m">
      <Header variant="h1">Task Management Dashboard</Header>

      <Container>
        <SpaceBetween size="s">
          <TaskTable />
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
