'use client';

import Link from 'next/link';

interface MigrationAssistantVersionProps {
  versionIdentifier: string;
  commitSha: string;
  commitDate: Date;
}

export default function MigrationAssistantVersion({
  versionIdentifier,
  commitSha ,
  commitDate
}: MigrationAssistantVersionProps) {
  return (
    <>
      <p>
        Migration Assistant version <code>{versionIdentifier}</code>.
      </p>
      <p>
        Built from commit{' '}
        <Link href="https://github.com/opensearch-project/opensearch-migrations/commits/">
          <code>{commitSha}</code>
        </Link>{' '}
        on <code>{commitDate.toLocaleDateString()}</code>.
      </p>
    </>
  );
}
