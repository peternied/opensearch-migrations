'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import { StatusIndicator } from '@cloudscape-design/components';

export default function MigrationAssistantStatusPage() {

  return (
    <SpaceBetween size="m">
      <Header variant="h1">
        Migration Assistant
      </Header>

      <Container>
        <Box>
          <Header variant="h3"><StatusIndicator type='warning'>Experimental</StatusIndicator></Header>
            This website is in an experimental phase. Features may change without notice,
            and backward compatibility is not guaranteed.
        </Box>
      </Container>
    </SpaceBetween>
  );
}
