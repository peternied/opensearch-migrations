'use client';

import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import MigrationAssistantVersion from './migration-assistant-version';
import {COMMIT_RECENT_TAG, COMMIT_SHA, COMMIT_DATE} from '@/lib/env';

export default function Page() {

  return (
    <SpaceBetween size="m">
      <Header variant="h1">About Migration Assistant</Header>

      <Container>
        <SpaceBetween size="s">
          <MigrationAssistantVersion
            versionIdentifier={COMMIT_RECENT_TAG}
            commitSha={COMMIT_SHA}
            commitDate={new Date(COMMIT_DATE)}
          />
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
