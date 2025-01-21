'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';

export default function Page() {

  return (
    <SpaceBetween size="m">
      <Header variant="h1">Status</Header>

      <Container>
        <SpaceBetween size="s">
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
