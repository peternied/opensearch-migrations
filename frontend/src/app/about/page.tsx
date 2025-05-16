'use client';

import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import MigrationAssistantVersion from '@/components/migration-assistant-version';
import { COMMIT_RECENT_TAG, COMMIT_SHA, COMMIT_DATE } from '@/lib/env';
import { Container } from '@cloudscape-design/components';

export default function Page() {
  return (
    <Container header={      <Header variant="h1">About Migration Assistant</Header>}>
        <MigrationAssistantVersion
          versionIdentifier={COMMIT_RECENT_TAG}
          commitSha={COMMIT_SHA}
          commitDate={new Date(COMMIT_DATE)}
        />
    </Container>
  );
}
