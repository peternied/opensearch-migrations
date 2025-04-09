'use client';

import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import Link from '@cloudscape-design/components/link';
import MigrationEntityTable, { MigrationEntity } from './entity-table';

const indexes: MigrationEntity[] = [
  { name: 'geonames', status: 'success' },
  { name: 'nyc_taxis', status: 'success' },
  { name: 'percolator', status: 'success' },
  {
    name: 'logs-181998',
    status: 'error',
    message:
      'IndexMappingTypeRemoval unsupported. Specify --multi-type-behavior.'
  },
  { name: 'logs-191998', status: 'success' },
  { name: 'logs-201998', status: 'success' },
  { name: 'logs-211998', status: 'success' }
];
const indexTemplates: MigrationEntity[] = [
  { name: 'daily_logs', status: 'success' }
];
const componentTemplates: MigrationEntity[] = [];

const aliases: MigrationEntity[] = [{ name: 'logs-all', status: 'success' }];

export default function MetadataMigration() {
  return (
    <SpaceBetween size="l">
      <Container header={<Header variant="h2">Migrated Items</Header>}>
        <SpaceBetween size="m">
          <MigrationEntityTable
            items={indexes}
            label="Indexes"
            mode="migration"
          />
          <MigrationEntityTable
            items={indexTemplates}
            label="Index Templates"
            mode="migration"
          />
          <MigrationEntityTable
            items={componentTemplates}
            label="Component Templates"
            mode="migration"
          />
          <MigrationEntityTable
            items={aliases}
            label="Aliases"
            mode="migration"
          />
        </SpaceBetween>
      </Container>

      <Container header={<Header variant="h2">Result</Header>}>
        <SpaceBetween size="m">
          <StatusIndicator type="success">
            No migration issues detected
          </StatusIndicator>
          <StatusIndicator type="info">
            See full migration log at{' '}
            <Link
              href="file:///tmp/meta_migrate_1720710618.log"
              external={true}
            >
              /tmp/meta_migrate_1720710618.log
            </Link>
          </StatusIndicator>
        </SpaceBetween>
      </Container>

      <Container header={<Header variant="h2">Issues</Header>}>
        <SpaceBetween size="s">
          <StatusIndicator type="warning">
            Elasticsearch 7.10.2 is not specifically supported, migration ran as
            if 7.17.22
          </StatusIndicator>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
