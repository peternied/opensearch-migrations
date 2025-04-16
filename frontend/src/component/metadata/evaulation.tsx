'use client';

import Container from '@cloudscape-design/components/container';
import Header from '@cloudscape-design/components/header';
import SpaceBetween from '@cloudscape-design/components/space-between';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
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

export default function MetadataEvaluation() {
  return (
    <SpaceBetween size="l">
      <Container
        header={<Header variant="h2">Cluster Evaluation Results</Header>}
      >
        <SpaceBetween size="m">
          <MigrationEntityTable
            items={indexes}
            label="Indexes"
            mode="evaluation"
          />
          <MigrationEntityTable
            items={indexTemplates}
            label="Index Templates"
            mode="evaluation"
          />
          <MigrationEntityTable
            items={componentTemplates}
            label="Component Templates"
            mode="evaluation"
          />
          <MigrationEntityTable
            items={aliases}
            label="Aliases"
            mode="evaluation"
          />
        </SpaceBetween>
      </Container>

      <Container header={<Header variant="h2">Result</Header>}>
        <StatusIndicator type="error">
          1 migration issues detected
        </StatusIndicator>
      </Container>

      <Container header={<Header variant="h2">Issues</Header>}>
        <SpaceBetween size="s">
          <StatusIndicator type="error">
            <strong>logs-181998:</strong> IndexMappingTypeRemoval unsupported —{' '}
            <em>
              No multi type resolution behavior declared, specify
              --multi-type-behavior to process
            </em>
          </StatusIndicator>
          <StatusIndicator type="warning">
            Elasticsearch 7.10.2 is not specifically supported, attempting
            migration as if 7.17.22
          </StatusIndicator>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  );
}
