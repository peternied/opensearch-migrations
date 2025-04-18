'use client';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import { Button } from '@cloudscape-design/components';

export default function Page() {
  return (
    <SpaceBetween size="m">
      <Header variant="h1">Remove Migration Assistant</Header>

      <SpaceBetween size="s">
        <span>
          With all Migrations complete, do you want to remove migration
          assistant?
        </span>
        <Button variant="primary">Delete Migration Assistant</Button>
      </SpaceBetween>
    </SpaceBetween>
  );
}
