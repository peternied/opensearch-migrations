import Header from '@cloudscape-design/components/header';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';

/**
 * TODO: look into what is happening here:
 * Warning: useLayoutEffect does nothing on the server, because its effect cannot be encoded into the server renderer's output format. This will lead to a mismatch between the initial, non-hydrated UI and the intended UI. To avoid this, useLayoutEffect should only be used in components that render exclusively on the client. See https://reactjs.org/link/uselayouteffect-ssr for common fixes.
 */

export async function getStaticProps() {
  const commitSha = process.env.COMMIT_SHA || 'unknown';
  const commitDate = process.env.COMMIT_DATE || 'unknown';

  return {
    props: { commitSha, commitDate }
  };
}

export default function About({
  commitSha,
  commitDate
}: {
  commitSha: string;
  commitDate: string;
}) {
  return (
    <SpaceBetween size="m">
      <Header variant="h1">About Migration Assistant</Header>

      <Container>
        <SpaceBetween size="s">
          <span>
            Migration Assistant was built from commit <code>{commitSha}</code>{' '}
            on <code>{commitDate}</code>.
          </span>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
