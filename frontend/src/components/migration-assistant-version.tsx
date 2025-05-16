'use client';

import { Box } from '@cloudscape-design/components';
import Link from 'next/link';

interface MigrationAssistantVersionProps {
  versionIdentifier: string;
  commitSha: string;
  commitDate: Date;
}

export default function MigrationAssistantVersion({
  versionIdentifier,
  commitSha,
  commitDate
}: MigrationAssistantVersionProps) {
  return (
    <>
      <Box variant="p">
        Migration Assistant version <Box variant="code">{versionIdentifier}</Box>.
      </Box>
      <Box variant="p">
        Built from commit{' '}
        <Link
          external
          href={`https://github.com/opensearch-project/opensearch-migrations/commit/${commitSha}`}
        >
        <Box variant="code">{commitSha}</Box>
        </Link>{' '}
        on <Box variant="code">{commitDate.toLocaleDateString()}</Box>.
      </Box>
    </>
  );
}
