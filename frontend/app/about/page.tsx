'use client';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import MigrationAssistantVersion from './migration-assistant-version';


export default function Page() {

  const commitRecentTag = process.env.COMMIT_RECENT_TAG!;
  const commitSha = process.env.COMMIT_SHA!;
  const commitDate = new Date(process.env.COMMIT_DATE!);
  
  return (
    <SpaceBetween size="m">
      <Header variant="h1">About Migration Assistant</Header>

      <Container>
        <SpaceBetween size="s">
        <MigrationAssistantVersion versionIdentifier={commitRecentTag}  />
          <span>
            Built from commit <code>{commitSha}</code> on{' '} <code>{commitDate.toLocaleDateString()}</code>.
          </span>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
