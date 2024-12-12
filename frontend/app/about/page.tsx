'use client';
import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';

export default function Page() {

  const commitSha = process.env.COMMIT_SHA;
  const commitDate = new Date(process.env.COMMIT_DATE!);
  
  return (
    <SpaceBetween size="m">
      <Header variant="h1">About Migration Assistant</Header>

      <Container>
        <SpaceBetween size="s">
          <span>
            Migration Assistant was built from commit <code>{commitSha}</code> on{' '}
            <code>{commitDate.toLocaleDateString()}</code>.
          </span>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
